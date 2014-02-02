#!/usr/bin/env python2
import os, shutil, tagm, sys, StringIO, unittest

class TagmCommandTestCase( unittest.TestCase ):
    def setUp( self ):
        self.oldout, self.olderr = sys.stdout, sys.stderr

        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()

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
    pass

class TestGetObjsByTags( TagmCommandGetTestCase ):
    pass
    
class TestGetTagsByTags( TagmCommandGetTestCase ):
    pass

class TestGetTagsByObjs( TagmCommandGetTestCase ):
    pass

def test_get_objs_by_tags():
    # Ensure db and tagged objects are setup
    test_add_tags()
    
    out = test_cmd( [ 'get', 'a,b' ] )
    assert out == 'obj2\nobj3\n'
    out = test_cmd( [ 'get', 'a,e:f' ] )
    assert out == 'obj1\n'
    out = test_cmd( [ 'get', '--subtags', 'a,e' ] )
    assert out == 'obj1\n'
    out = test_cmd( [ 'get' ] )
    assert out == 'obj1\nobj2\nobj3\n'

def test_get_tags_by_tags():
    # Ensure db and tagged objects are setup
    test_add_tags()
    
    out = test_cmd( [ 'get', '--tags', 'a,b' ] )
    assert out == 'c\nd\n'
    out = test_cmd( [ 'get', '--tags', 'e:f' ] )
    assert out == 'a\nd\n'
    out = test_cmd( [ 'get', '--tags', '--subtags', 'e' ] )
    assert out == 'a\nd\ne:f\n'
    out = test_cmd( [ 'get', '--tags' ] )
    assert out == 'a\nb\nc\nd\ne:f\n'

def test_get_tags_by_objs():
    test_add_tags()
    
    out = test_cmd( [ 'get', '--obj-tags', 'obj1' ] )
    assert out == 'a\nd\ne:f\n'
    out = test_cmd( [ 'get', '--obj-tags', 'obj2,obj3' ] )
    assert out == 'a\nb\nd\n'
    out = test_cmd( [ 'get', '--obj-tags' ] )
    assert out == ''
'''
def test_cmd( cmd, no_err = True, grab_std = True ):
    if grab_std:
        # Highjack stdout and stderr for a bit
        oldout, olderr = sys.stdout, sys.stderr

        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
    
    try:
    finally:
        if grab_std:
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
        
            # Restore stds before return
            sys.stdout, sys.stderr = oldout, olderr
        else:
            stdout = stderr = ''

    if no_err:
        assert stderr == ''
        
        return stdout
    
    return stdout, stderr

def run_test( test_func ):
    print 'Running %s...' % test_func.__name__,
    
    # create test-data folder
    os.mkdir( 'test-data' )
    os.chdir( 'test-data' )
    
    try:
        test_func()
    finally:
        # remove test-data folder along with any files in it.
        os.chdir( '..' )
        shutil.rmtree( 'test-data' )
    
    print 'Passed!'

def run_all_tests():
    run_test( test_init )

    run_test( test_add_tags )
    
    run_test( test_get_objs_by_tags )
    
    run_test( test_get_tags_by_tags )
    
    run_test( test_get_tags_by_objs )
    
    run_test( test_glob_add )
    
    run_test( test_add_symlink )
    
    run_test( test_add_symlink_no_follow )
'''
if __name__ == '__main__':
    unittest.main()
