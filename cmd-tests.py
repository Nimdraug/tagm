from subprocess import Popen, PIPE
import os, shutil

def test_init():
    #python2 tagm.py init'
    # Should result in a .tagm.db file being created
    out, err = test_cmd( [ 'init' ] )
    
    assert out == 'Initiated tagm database in .tagm.db\n'
    assert err == ''
    assert os.stat( '.tagm.db' )

def test_add_tags():
    # Ensure db is setup
    test_init()
    
    # Add some files
    os.mknod( 'obj1' )
    os.mknod( 'obj2' )
    os.mknod( 'obj3' )
    
    out, err = test_cmd( [ 'add', 'a', 'obj1' ] )
    assert out == 'Added obj1 with tags a\n'
    assert err == ''
    test_cmd( [ 'add', 'a,b', 'obj2' ] )
    assert out == 'Added obj2 with tags a,b\n'
    assert err == ''
    test_cmd( [ 'add', 'a,b,c', 'obj3' ] )
    assert out == 'Added obj3 with tags a,b,c\n'
    assert err == ''
    test_cmd( [ 'add', 'd', 'obj1,obj2,obj3' ] )
    assert out == 'Added obj1,obj2,obj2 with tags d\n'
    assert err == ''

def test_cmd( cmd ):
    proc = Popen( [ '../tagm.py' ] + cmd, stdout = PIPE, stderr = PIPE )
    
    stdout, stderr = proc.communicate()
    
    assert proc.returncode == 0
    
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
    
    #run_test( test_get_objs_by_tags )
    
    #run_test( test_get_tags_by_tags )
    
    #run_test( test_get_tags_by_objs )

if __name__ == '__main__':
    run_all_tests()
