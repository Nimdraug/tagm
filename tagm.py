#!/bin/env python2
import os.path
import sqlite3

# == Terms ==
# tag           ie. Sweden
# tagpath       ie. Earth:Europe:Sweden
# tagpaths      ie. Earth:Europe:Sweden,Building:Residentual
# subtag        ie. in Earth:Europe, Europe is a subtag of Earth
# leaftag       ie. in Earth:Europe:Sweden, Sweden is the leaftag
# obj           ie. /home/user/documents/a.txt
#               or  http://www.example.com/url/file.txt
# objs          ie. [ obj, ... ]

class TagNotFoundError( Exception ):
    pass

class DBNotFoundError( Exception ):
    pass

class TagmDB( object ):
    def __init__( self, dbfile = None ):
        # TODO: move the db file searching code out to cmd part
        if dbfile == None:
            # Try and find a .tagr.db file in current dir, if not there continue going up the filetree
            # if nothing found, error will be raised.
            curpath = os.path.realpath( '.' )
            while 1:
                if os.path.exists( os.path.join( curpath, '.tagm.db' ) ):
                    self.dbpath = curpath
                    break
                elif curpath == '/':
                    raise DBNotFoundError, 'Could not find tagm database'
                else:
                    curpath = os.path.realpath( curpath + '/..' )
            self.db = sqlite3.connect( os.path.join( self.dbpath, '.tagm.db' ) )
        else:
            self.dbpath = os.path.split( dbfile )[0]
            self.db = sqlite3.connect( dbfile )

       
        self.db.row_factory = sqlite3.Row
        try:
            self.db.execute( 'select * from tags' )

        except sqlite3.OperationalError:
            # Table does not exist, create it!

            # Objs ( rowid, path )
            self.db.execute( 'create table objs ( path )' )
            
            # Tags ( rowid, tag, parent )
            self.db.execute( 'create table tags ( tag, parent )' )
            
            # ObjTags ( rowid, tag_id, obj_id )
            self.db.execute( 'create table objtags ( tag_id, obj_id )' )
            
            self.db.commit()

    # Private util methods
    def _parse_tagpaths( self, tagpaths ):
        '''Cleans up tagpaths and returns them as a lists instead of a colon sep string'''
        return [ [ tag.strip() for tag in tagpath.split( ':' ) ] for tagpath in tagpaths ]

    def _get_tag_ids( self, parsed_tagpaths, create = False ):
        '''Takes a list of tagpaths and returns the tag id of the leaf nodes'''
        
        tag_ids = []
        for tagpath in parsed_tagpaths:
            pid = 0
            for tag in tagpath:
                row = self.db.execute( "select rowid from tags where tag = ? and parent = ?", ( tag, pid ) ).fetchone()
                
                if not row:
                    if create:
                        pid = self.db.execute( "insert into tags ( tag, parent ) values ( ?, ? )", ( tag, pid ) ).lastrowid
                    else:
                        raise TagNotFoundError
                else:
                    pid = row['rowid']
                
            tag_ids.append( pid )
        return tag_ids
    
    def _get_subtag_ids( self, tag_id ):
        '''Gets the subtags for the specified tag_id. Will search recursively'''
        subtags = []
                
        query = 'select rowid from tags where parent = ?'
        for tag in self.db.execute( query, [ tag_id ] ):
            subtags.append( tag['rowid'] )
            
            subtags += self._get_subtag_ids( tag['rowid'] )
        
        return subtags

    def _get_tagpath( self, tag_id ):
        '''Gets the tagpath for the specifed tag_id'''
        row = self.db.execute( 'select parent, tag from tags where rowid = ?', [tag_id] ).fetchone()
        
        tagnames = []
        
        if not row:
            raise TagNotFoundError

        if row['parent']:
            tagnames += self._get_tagpath( row['parent'] )
        tagnames.append( row['tag'] )
        
        return tagnames
    
    def _get_obj_ids( self, objs ):
        # TODO: Should raise exception on nonexisting objects like _get_tag_ids
        #       Will currently cause tags to be returned for objects which dont have
        #       any of the tags presented. Could cause unexpected behavior.
        query = "select rowid from objs where path in ( '" + "','".join( objs ) + "' )"
        
        return [ row['rowid'] for row in self.db.execute( query ) ]
    
    # Public methods
    def add( self, tagpaths, objs = None, find = None ):
        '''
            Adds tags to the specified objects
        '''
        tags = self._parse_tagpaths( tagpaths )
        tags = self._get_tag_ids( tags, True )
        
        # If no objs, find can be used to search internaly for objs
        if not objs:
            objs = self.get( find )
        elif isinstance( objs, basestring ):
            objs = [ objs ]
        
        for obj in objs:
            if not os.path.exists( obj ):
                raise Exception, '%s not found' % obj

            # Add object
            obj = os.path.relpath( obj, self.dbpath )
            
            row = self.db.execute( 'select rowid from objs where path = ?', [obj] ).fetchone()
            
            if not row:
                curs = self.db.execute( 'insert into objs ( path ) values ( ? )', ( obj, ) )
                obj_id = curs.lastrowid
            else:
                obj_id = row['rowid']
            
            for i, tag_id in enumerate( tags ):
                self.db.execute( 'insert into objtags ( tag_id, obj_id ) values ( ?, ? )', ( tag_id, obj_id ) )
        
        self.db.commit()

    def get( self, tagpaths, obj_tags = False, subtags = False ):
        '''
            Looks up the objects tagged by the leaftags (or the leaftags' subtags if subtags is True)
            and returns the objects themselves, or if obj_tags is True, returns any further tags the
            objects are tagged with that are not part of the queried tags.
            
            Example:
            If you have objects 1, 2 and 3, and the tags a, b and c.
            And object 1 is tagged with a, object 2 with a and b, and
            object 3 with a, b and c. Then querying for tags a and b
            will return objects 2 and 3, and if obj_tags is True, the tag
            c will be returned instead, giving the caller a listing of
            what tags are available to further constrain its queries.
        '''
        try:
            # Split tagpaths up into individual tags
            tags = self._parse_tagpaths( tagpaths )
            
            # Lookup the leaftag ids
            tagids = self._get_tag_ids( tags )

            # If required, recursively include all of the subtags of the leaftags
            # TODO: subtags as recursion depth _get_subtag_ids( tid, subtags )
            if subtags:
                tagids = [ [ tid ] + self._get_subtag_ids( tid ) for tid in tagids ]
            else:
                tagids = [ [ tid ] for tid in tagids ]
        except TagNotFoundError:
            # One of the tags provided does not exist, thus no query is needed as nothing will be found.
            return []
        
        # Start constructing the query
        where = []
        query_tags = []
        query = ''
        
        for i, tagid in enumerate( tagids ):
            if i > 0:
                query += " left join objtags as t%s on ( t0.obj_id = t%s.obj_id  )" % ( i, i )

            if len( tagid ) > 1:
                # subtags is True, obj can have any of the listed tags
                query_tags += tagid
                where.append( 't%s.tag_id in ( %s )' % ( i, ', '.join( [ '?' ] * len( tagid ) ) ) )
            else:
                query_tags.append( tagid[0] )
                where.append( 't%s.tag_id = ?' % ( i ) )

        # TODO: Rearrange?
        if not obj_tags:
            query = "select distinct o.path from objtags as t0" + query
            query += ' left join objs as o on ( t0.obj_id = o.rowid )'
        else:
            query = "select distinct tt.tag_id from objtags as t0" + query
            query += ' left join objtags as tt on ( tt.obj_id = t0.obj_id and tt.tag_id not in ( %s ) )' % ','.join( [ str( tagid[0] ) for tagid in tagids ] )
            where.append( 'tt.tag_id not null' )
        
        query += ' where ' + ' and '.join( where )
        
        curs = self.db.execute( query, query_tags )

        if not obj_tags:
            return [ obj['path'] for obj in curs ]
        else:
            return [ ':'.join( self._get_tagpath( row[0] ) ) for row in curs ]
            
    def get_obj_tags( self, objs ):
        query = "select distinct o0.tag_id from objtags as o0"
        where = []

        objs = self._get_obj_ids( [ os.path.relpath( obj, self.dbpath ) for obj in objs ] )
        
        for i, obj in enumerate( objs ):
            if i > 0:
                query += " left join objtags as o%s on ( o0.tag_id = o%s.tag_id )" % ( i, i )
            
            where.append( 'o%s.obj_id = ?' % ( i ) )
        
        
        query += ' where ' + ' and '.join( where )
        
        objtags = []
        
        for row in self.db.execute( query, objs ):
            objtags.append( ':'.join( self._get_tagpath( row['tag_id'] ) ) )
        
        return objtags

def setup_parser():
    import argparse, sys

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Init command: Initializes new tagm db file
    def do_init( db, ns ):
        db = TagmDB( '.tagm.db' )
        print 'Initiated tagm database in .tagm.db'
    
    init_parser = subparsers.add_parser( 'init', description = 'Will initialzie a tagm database in a file called .tagm.db located in the current directory' )
    init_parser.set_defaults( func = do_init )
    
    # Add command: Adds tags to objects
    def do_add( db, ns ):
        db.add( ns.tags.split(','), ns.objs )
        for f in ns.objs:
            print 'Added', f, 'with tags', ns.tags

    add_parser = subparsers.add_parser( 'add', description = 'Will add the specified tags to the specified objects' )
    add_parser.add_argument( 'tags', help = 'List of tagpaths separated by comma' )
    add_parser.add_argument( 'objs', nargs = '+', help = 'List of objects to be tagged' )
    add_parser.set_defaults( func = do_add )

    # Get command: gets objects tagged with tags
    def do_get( db, ns ):
        objs = db.get( ns.tags.split(','), obj_tags = ns.obj_tags )
        if not ns.obj_tags:
            for obj in objs:
                print os.path.relpath( os.path.join( db.dbpath, obj ) )
        else:
            for tag in sorted( objs ):
                print tag
            
    get_parser = subparsers.add_parser( 'get', description = 'Will list all the objects that are taged with all of the specified tags.' )
    get_parser.add_argument( 'tags', help = 'List of tagpaths separated by comma' )
    get_parser.add_argument( '--tags', action = 'store_true', dest = 'obj_tags' )
    get_parser.set_defaults( func = do_get )
    
    return parser

if __name__ == '__main__':
    args = setup_parser().parse_args()

    if args.func.__name__ != 'do_init':
        try:
            db = TagmDB()
        except DBNotFoundError:
            print 'Unable to find tagm database!'
            print 'Please create one by running:'
            print '%s init' % sys.argv[0]
            sys.exit(1)
    else:
        db = None
    
    args.func( db, args )
