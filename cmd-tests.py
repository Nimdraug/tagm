#!/usr/bin/env python2
import os, shutil, tagm, sys, StringIO, unittest

class TagmCommandTestCase( unittest.TestCase ):
    def setUp( self ):
        self.oldout, self.olderr = sys.stdout, sys.stderr

        self.stdout = sys.stdout = StringIO.StringIO()
        self.stderr = sys.stderr = StringIO.StringIO()

        os.mkdir( 'test-data' )
        os.chdir( 'test-data' )

        self.db = tagm.TagmDB( '.tagm.db' )

        self.addCleanup( self.cleanup_files )

    def run_command( self, cmd ):
        args = tagm.setup_parser().parse_args( cmd )
        
        args.func( self.db, '', args )
        
        stdout = sys.stdout.getvalue()
        stderr = sys.stderr.getvalue()
        
        sys.stdout.truncate( 0 )
        sys.stderr.truncate( 0 )
        
        return stdout, stderr
        
    def tearDown( self ):
        sys.stdout = self.oldout
        sys.stderr = self.olderr

    def cleanup_files( self ):
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

    def test_get_no_obj( self ):
        out, err = self.run_command( [ 'get', '--obj-tags' ] )
        self.assertEqual( out, '' )

if __name__ == '__main__':
    unittest.main()
