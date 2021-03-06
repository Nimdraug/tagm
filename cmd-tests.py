#!/usr/bin/env python2
import os, shutil, tagm, sys, StringIO, unittest

class TagmCommandTestCase( unittest.TestCase ):
    def setUp( self ):
        os.mkdir( 'test-data' )
        os.chdir( 'test-data' )

        self.db = tagm.TagmDB( '.tagm.db' )

    def run_command( self, cmd ):
        args = tagm.setup_parser().parse_args( cmd )

        self.oldout, self.olderr = sys.stdout, sys.stderr

        self.stdout = sys.stdout = StringIO.StringIO()
        self.stderr = sys.stderr = StringIO.StringIO()
        
        args.func( self.db, '', args )
        
        stdout = sys.stdout.getvalue()
        stderr = sys.stderr.getvalue()
        
        sys.stdout.truncate( 0 )
        sys.stderr.truncate( 0 )

        sys.stdout = self.oldout
        sys.stderr = self.olderr
        
        return stdout, stderr
        
    def tearDown( self ):
        os.chdir( '..' )
        shutil.rmtree( 'test-data' )


class TestInit( TagmCommandTestCase ):
    def runTest( self ):
        out,err = self.run_command( [ 'init' ] )
        
        self.assertEqual( out, 'Initiated tagm database in .tagm.db\n' )
        self.assertTrue( os.stat( '.tagm.db' ) )

class TestAdd( TagmCommandTestCase ):
    def setUp( self ):
        super( TestAdd, self ).setUp()

        os.mknod( 'obj1' )
        os.mknod( 'obj2' )

    def test_add_single_tag( self ):
        out, err = self.run_command( [ 'add', 'a', 'obj1' ] )
        self.assertEqual( out, 'Added obj1 with tags a\n' )
    
    def test_add_multiple_tags( self ):
        out, err = self.run_command( [ 'add', 'a,b', 'obj2' ] )
        self.assertEqual( out, 'Added obj2 with tags a,b\n' )
    
    def test_add_multiple_objs( self ):
        out, err = self.run_command( [ 'add', 'c', 'obj1', 'obj2' ] )
        self.assertEqual( out, (
            'Added obj1 with tags c\n'
            'Added obj2 with tags c\n'
        ) )

    def test_add_subtag( self ):
        out, err = self.run_command( [ 'add', 'a:b', 'obj1' ] )
        self.assertEqual( out, 'Added obj1 with tags a:b\n' )
        
    def test_add_escaped_colon( self ):
        out, err = self.run_command( [ 'add', 'a\\:', 'obj1' ] )
        self.assertEqual( out, 'Added obj1 with tags a\\:\n' )

        curs = self.db.db.execute( 'select * from tags' )
        self.assertEqual( curs.fetchall()[0]['tag'], 'a:' )

    def test_add_unicode_obj( self ):
        fname = u'\xe5\xe4\xf6'
        os.mknod( fname.encode( sys.getfilesystemencoding() ) )
        out, err = self.run_command( [ 'add', 'a', fname ] )
        self.assertEqual( out, u'Added %s with tags a\n' % fname )

    def test_add_unicode_tag( self ):
        tag = u'\xe5\xe4\xf6'
        out, err = self.run_command( [ 'add', tag, 'obj1' ] )
        self.assertEqual( out, u'Added obj1 with tags %s\n' % tag )

class TestAddGlob( TagmCommandTestCase ):
    def setUp( self ):
        super( TestAddGlob, self ).setUp()

        os.mkdir( 'dir1' )
        os.mknod( 'dir1/obj1' )
        os.mkdir( 'dir1/dir2' )
        os.mknod( 'dir1/dir2/obj2' )
        os.mkdir( 'dir1/dir2/dir3' )
        os.mknod( 'dir1/dir2/dir3/obj3' )

    def test_add_single_obj( self ):
        out, err = self.run_command( [ 'add', 'a', '-r', '*/obj1' ] )
        self.assertEqual( out, 'Added dir1/obj1 with tags a\n' )
    
    def test_add_multiple_obj( self ):
        out, err = self.run_command( [ 'add', 'b', '-r', '*/obj*' ] )
        self.assertEqual( out, (
            'Added dir1/obj1 with tags b\n'
            'Added dir1/dir2/obj2 with tags b\n'
            'Added dir1/dir2/dir3/obj3 with tags b\n'
        ) )

    def test_add_with_unicode( self ):
        fname = u'\xe5\xe4\xf6'
        os.mknod( ( u'dir1/dir2/dir3/%s' % fname ).encode( sys.getfilesystemencoding() ) )
        out, err = self.run_command( [ 'add', 'a', '-r', 'dir1/dir2/dir3/*' ] )
        self.assertEqual( out.decode( 'UTF-8' ), ( 
            u'Added dir1/dir2/dir3/obj3 with tags a\n'
            u'Added dir1/dir2/dir3/%s with tags a\n' % fname
        ) )

    
class TestAddSymlink( TagmCommandTestCase ):
    def setUp( self ):
        super( TestAddSymlink, self ).setUp()

        os.mknod( 'obj1' )
        os.mkdir( 'dir1' )
        os.symlink( '../obj1', 'dir1/obj2' )

    def test_add_symlink( self ):
        out, err = self.run_command( [ 'add', 'a', 'dir1/obj2' ] )
        self.assertEqual( out, 'Added obj1 with tags a\n' )

        # Ensure the symlink was infact followed
        out, err = self.run_command( [ 'get', 'a' ] )
        self.assertEqual( out, 'obj1\n' )
    
    def test_add_symlink_no_follow( self ):
        out, err = self.run_command( [ 'add', '--no-follow', 'a', 'dir1/obj2' ] )
        self.assertEqual( out, 'Added dir1/obj2 with tags a\n' )

        # Ensure the symlink was not followed
        out, err = self.run_command( [ 'get', 'a' ] )
        self.assertEqual( out, 'dir1/obj2\n' )


class TagmCommandGetTestCase( TagmCommandTestCase ):
    def setUp( self ):
        super( TagmCommandGetTestCase, self ).setUp()

        os.mknod( 'obj1' )
        os.mknod( 'obj2' )
        os.mknod( 'obj3' )
        os.mknod( 'obj4' )
         
        self.db.add( [ 'a' ], [ 'obj1', 'obj2', 'obj3' ] )
        self.db.add( [ 'b' ], [ 'obj2', 'obj3' ] )
        self.db.add( [ 'c' ], [ 'obj3' ] )
        self.db.add( [ [ 'c', 'd' ] ], [ 'obj1' ] )

class TestGetObjsByTags( TagmCommandGetTestCase ):
    def test_get_single_tag( self ):
        out, err = self.run_command( [ 'get', 'b' ] )
        self.assertEqual( out, 'obj2\nobj3\n' )

    def test_get_multiple_tags( self ):
        out, err = self.run_command( [ 'get', 'b,c' ] )
        self.assertEqual( out, 'obj3\n' )
    
    def test_get_subtag( self ):
        out, err = self.run_command( [ 'get', 'c:d' ] )
        self.assertEqual( out, 'obj1\n' )

    def test_get_subtag_parent_include_subtags( self ):
        out, err = self.run_command( [ 'get', '--subtags', 'c' ] )
        self.assertEqual( out, 'obj3\nobj1\n' )

    def test_get_unicode_tag( self ):
        tag = u'\xe5\xe4\xf6'
        self.db.add( [[tag]], ['obj1'] )
        out, err = self.run_command( [ 'get', tag ] )
        self.assertEqual( out, 'obj1\n' )


    
class TestGetTagsByTags( TagmCommandGetTestCase ):
    def test_get_single_tag( self ):
        out, err = self.run_command( [ 'get', '--tags', 'b' ] )
        self.assertEqual( out, 'a\nc\n' )

    def test_get_multiple_tags( self ):
        out, err = self.run_command( [ 'get', '--tags', 'b,c' ] )
        self.assertEqual( out, 'a\n' )
    
    def test_get_subtag( self ):
        out, err = self.run_command( [ 'get', '--tags', 'c:d' ] )
        self.assertEqual( out, 'a\n' )

    def test_get_subtag_parent_include_subtags( self ):
        out, err = self.run_command( [ 'get', '--tags', '--subtags', 'c' ] )
        self.assertEqual( out, 'a\nb\nc:d\n' )

class TestGetTagsByObjs( TagmCommandGetTestCase ):
    # TODO: Add test for non existing file
    def test_get_single_obj( self ):
        out, err = self.run_command( [ 'get', '--obj-tags', 'obj1' ] )
        self.assertEqual( out, 'a\nc:d\n' )

    def test_get_multiple_obj( self ):
        out, err = self.run_command( [ 'get', '--obj-tags', 'obj2', 'obj3' ] )
        self.assertEqual( out, 'a\nb\n' )

    def test_get_invalid_obj( self ):
        out, err = self.run_command( [ 'get', '--obj-tags', 'obj4' ] )
        self.assertEqual( out, '' )

    def test_get_unicode_tag( self ):
        tag = u'\xe5\xe4\xf6'
        self.db.add( [[tag]], ['obj4'] )
        out, err = self.run_command( [ 'get', '--obj-tags', 'obj4' ] )
        self.assertEqual( out.decode( 'UTF-8' ), u'%s\n' % tag )

    def test_get_no_obj( self ):
        out, err = self.run_command( [ 'get', '--obj-tags' ] )
        self.assertEqual( out, '' )

class TestGetEscapedColon( TagmCommandTestCase ):
    def setUp( self ):
        super( TestGetEscapedColon, self ).setUp()
        
        os.mknod( 'obj1')
        
        self.db.add( [ [ 'a:' ] ], [ 'obj1' ] )
        
    def runTest( self ):
        out, err = self.run_command( [ 'get', '--tags' ] )
        self.assertEqual( out, 'a\\:\n' )

class TestSet( TagmCommandTestCase ):
    def setUp( self ):
        super( TestSet, self ).setUp()

        os.mknod( 'obj1' )

    def test_set( self ):
        out, err = self.run_command( [ 'set', 'a', 'obj1' ] )
        self.assertEqual( out, 'Set tags to a on obj1\n' )

    def test_set_tags( self ):
        self.db.add( [ [ 'a' ] ], [ 'obj1' ] )
        out, err = self.run_command( [ 'set', 'b', '--tags', 'a' ] )

        self.assertEqual( out, 'Set tags to b on obj1\n' )

        self.assertEqual( self.db.get( [ [ 'a' ] ] ), [] )
    
if __name__ == '__main__':
    unittest.main()
