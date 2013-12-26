import os, shutil, tagm, sys, StringIO

def test_init():
    #python2 tagm.py init'
    # Should result in a .tagm.db file being created
    out = test_cmd( [ 'init' ] )
    
    assert out == 'Initiated tagm database in .tagm.db\n'
    assert os.stat( '.tagm.db' )

def test_add_tags():
    # Ensure db is setup
    test_init()
    
    # Add some files
    os.mknod( 'obj1' )
    os.mknod( 'obj2' )
    os.mknod( 'obj3' )
    
    out = test_cmd( [ 'add', 'a', 'obj1' ] )
    assert out == 'Added obj1 with tags a\n'
    out = test_cmd( [ 'add', 'a,b', 'obj2' ] )
    assert out == 'Added obj2 with tags a,b\n'
    out = test_cmd( [ 'add', 'a,b,c', 'obj3' ] )
    assert out == 'Added obj3 with tags a,b,c\n'
    out = test_cmd( [ 'add', 'd', 'obj1', 'obj2', 'obj3' ] )
    assert out == (
        'Added obj1 with tags d\n'
        'Added obj2 with tags d\n'
        'Added obj3 with tags d\n'
    )
    out = test_cmd( [ 'add', 'e:f', 'obj1' ] )
    assert out == 'Added obj1 with tags e:f\n'

def test_glob_add():
    test_init()
    
    # Create the temporary dir structure
    os.mkdir( 'dir1' )
    os.mknod( 'dir1/obj1' )
    os.mkdir( 'dir1/dir2' )
    os.mknod( 'dir1/dir2/obj2' )
    os.mkdir( 'dir1/dir2/dir3' )
    os.mknod( 'dir1/dir2/dir3/obj3' )
    
    out = test_cmd( [ 'add', 'a', '-r', '*/obj1' ] )
    assert out == 'Added dir1/obj1 with tags a\n'

    out = test_cmd( [ 'add', 'b', '-r', '*/obj*' ] )
    assert out == (
        'Added dir1/obj1 with tags b\n'
        'Added dir1/dir2/obj2 with tags b\n'
        'Added dir1/dir2/dir3/obj3 with tags b\n'
    )

def test_add_symlink():
    test_init()
    
    # Create file structure
    os.mknod( 'obj1' )
    os.mkdir( 'dir1' )
    os.symlink( '../obj1', 'dir1/obj2' )
    
    out = test_cmd( [ 'add', 'a', 'dir1/obj2' ] )
    assert out == 'Added obj1 with tags a\n'

    # Ensure the symlink was infact followed
    out = test_cmd( [ 'get', 'a' ] )
    assert out == 'obj1\n'

def test_add_symlink_no_follow():
    test_init()
    
    # Create file structure
    os.mknod( 'obj1' )
    os.mkdir( 'dir1' )
    os.symlink( '../obj1', 'dir1/obj2' )
    
    out = test_cmd( [ 'add', '--no-follow', 'a', 'dir1/obj2' ] )
    assert out == 'Added dir1/obj2 with tags a\n'

    # Ensure the symlink was not followed
    out = test_cmd( [ 'get', 'a' ] )
    assert out == 'dir1/obj2\n'

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
    assert out == 'a\nb\nc\nd\ne:f\n'

def test_cmd( cmd, no_err = True, grab_std = True ):
    if grab_std:
        # Highjack stdout and stderr for a bit
        oldout, olderr = sys.stdout, sys.stderr

        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
    
    try:
        args = tagm.setup_parser().parse_args( cmd )
        
        db = tagm.TagmDB( '.tagm.db' ) if cmd[0] != 'init' else None

        args.func( db, '', args )
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

if __name__ == '__main__':
    run_all_tests()
