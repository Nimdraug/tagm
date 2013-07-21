from subprocess import Popen, PIPE
import os, shutil

def test_init():
    #python2 tagm.py init'
    # Should result in a .tagm.db file being created
    out, err = test_cmd( [ '../tagm.py', 'init' ] )
    
    assert out == 'Initiated tagm database in .tagm.db\n'
    assert err == ''

def test_cmd( cmd ):
    proc = Popen( cmd, stdout = PIPE, stderr = PIPE )
    
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

    #run_test( test_add_tags )
    
    #run_test( test_get_objs_by_tags )
    
    #run_test( test_get_tags_by_tags )
    
    #run_test( test_get_tags_by_objs )

if __name__ == '__main__':
    run_all_tests()
