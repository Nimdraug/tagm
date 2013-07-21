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
    assert out == 'Added obj1 with tags d\nAdded obj2 with tags d\nAdded obj3 with tags d\n'
    out = test_cmd( [ 'add', 'e:f', 'obj1' ] )
    assert out == 'Added obj1 with tags e:f\n'

def test_get_objs_by_tags():
    # Ensure db and tagged objects are setup
    test_add_tags()
    
    out = test_cmd( [ 'get', 'a,b' ] )
    assert out == 'obj2\nobj3\n'
    out = test_cmd( [ 'get', 'a,e:f' ] )
    assert out == 'obj1\n'

def test_get_tags_by_tags():
    # Ensure db and tagged objects are setup
    test_add_tags()
    
    out = test_cmd( [ 'get', '--tags', 'a,b' ] )
    assert out == 'c\nd\ne:f\n'
    out = test_cmd( [ 'get', '--tags', 'e:f' ] )
    assert out == 'a\n'
    

def test_cmd( cmd, no_err = True ):
    # Highjack stdout and stderr for a bit
    oldout, olderr = sys.stdout, sys.stderr

    sys.stdout = StringIO.StringIO()
    sys.stderr = StringIO.StringIO()
    
    try:
        args = tagm.setup_parser().parse_args( cmd )
        
        db = tagm.TagmDB() if cmd[0] != 'init' else None

        args.func( db, args )
    finally:
        stdout = sys.stdout.getvalue()
        stderr = sys.stderr.getvalue()
    
        # Restore stds before return
        sys.stdout, sys.stderr = oldout, olderr

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
    
    #run_test( test_get_tags_by_objs )

if __name__ == '__main__':
    run_all_tests()
