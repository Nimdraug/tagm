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

    def _new_get( self, tagpaths, obj_tags = False, subtags = False ):
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
        except TagNotFoundError:
            # One of the tags provided does not exist, thus no query is needed as nothing will be found.
            return []
        
        # Start constructing the query
        where = []
        query_tags = []
        query = ''
        
        for i, tag in enumerate( tags ):
            if i > 0:
                query += " left join objtags as t%s on ( t0.obj_id = t%s.obj_id  )" % ( i, i )

            if len( tag ) > 1:
                # subtags is True, obj can have any of the listed tags
                where.append( 't%s.tag_id in (%s)' % ( i, ','.join( [ str( t ) for t in tag ] ) ) )
            else:
                query_tags.append( tagids[i] )
                where.append( 't%s.tag_id = ?' % ( i ) )

        # TODO: Rearrange?
        if not obj_tags:
            query = "select distinct o.path from objtags as t0" + query
            query += ' left join objs as o on ( t0.obj_id = o.rowid )'
        else:
            query = "select tt.tag_id from objtags as t0" + query
            query += ' left join objtags as tt on ( tt.obj_id = t0.obj_id and tt.tag_id not in ( %s ) )' % ','.join( [ str( tag ) for tag in tagids ] )
            where.append( 'tt.tag_id not null' )
        
        query += ' where ' + ' and '.join( where )
        
        if obj_tags:
            # TODO: Optional?
            query += ' union select rowid from tags where parent in ( %s )' % ( ','.join( [ str( tag ) for tag in tagids ] ) )

        curs = self.db.execute( query, query_tags )

        if not obj_tags:
            return [ obj['path'] for obj in curs ]
        else:
            return [ ':'.join( self._get_tagpath( row[0] ) ) for row in curs ]
            

    def get( self, tagpaths ):
        '''
            Gets the objects that are tagged with all the tags in tagpath
        '''
        try:
            tags = self._parse_tagpaths( tagpaths )
            # Translate tagnames into tag ids
            tags = self._get_tag_ids( tags )
            # Get any subtags as well. Ie. objs tagged with earth:europe will be listed
            # when querying for earth
            tags = [ [ tag ] + self._get_subtag_ids( tag ) for tag in tags ]
        except TagNotFoundError:
            return []

        query = "select distinct o.path from objtags as t0"
        
        where = []
        
        query_tags = []
        
        for i, tag in enumerate( tags ):
            if i > 0:
                query += " left join objtags as t%s on ( t0.obj_id = t%s.obj_id  )" % ( i, i )

            if len( tag ) > 1:
                where.append( 't%s.tag_id in (%s)' % ( i, ','.join( [ str( t ) for t in tag ] ) ) )
            else:
                query_tags.append( tag[0] )
                where.append( 't%s.tag_id = ?' % ( i ) )
        
        query += ' left join objs as o on ( t0.obj_id = o.rowid ) where ' + ' and '.join( where )

        return [ obj['path'] for obj in self.db.execute( query, query_tags ) ]
        
    
    def get_tags( self, tagpaths ):
        try:
            tags = self._parse_tagpaths( tagpaths )
            tags = self._get_tag_ids( tags )
        except TagNotFoundError:
            return []
        
        query = "select tt.tag_id from objtags as t0"
        
        where = []
        
        for i, tag in enumerate( tags ):
            if i > 0:
                query += " left join objtags as t%s on ( t0.obj_id = t%s.obj_id  )" % ( i, i )

            where.append( 't%s.tag_id = ?' % ( i ) )
        
        query += ' left join objtags as tt on ( tt.obj_id = t0.obj_id and tt.tag_id not in ( %s ) )' % ','.join( [ str( tag ) for tag in tags ] )
        query += ' where ' + ' and '.join( where ) + ' and tt.tag_id not null'
        
        query += ' union select rowid from tags where parent in ( %s )' % ( ','.join( [ str( tag ) for tag in tags ] ) )
        
        curs = self.db.execute( query, tags )
        return [ ':'.join( self._get_tagpath( row[0] ) ) for row in curs ]

    def get_obj_tags( self, objs ):
        query = 'select distinct tag_id from objtags where obj_id in ( select rowid from objs where path in ( %s ) )'

        objs = [ os.path.relpath( obj, self.dbpath ) for obj in objs ]
        
        query = query % ( "'" + "','".join( objs ) + "'" )
        
        objtags = []
        
        for row in self.db.execute( query ):
            objtags.append( ':'.join( self._get_tagpath( row['tag_id'] ) ) )
        
        return objtags
