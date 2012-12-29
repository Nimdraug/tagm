import tagm
import sqlite3

db = None

def init_dummy_db():
    global db
    
    db = tagm.TagmDB( ':memory:' )

def test_add_tags():
    init_dummy_db()
    
    db.add( [ 'a', 'b', 'c' ], [ 'obj1', 'obj2' ] )
    db.add( [ 'd', 'e' ], [ 'obj1' ] )
    db.add( [ 'f', 'g' ], [ 'obj2' ] )

def test_get_objs_by_tags():
    test_add_tags()
    
    res = db.get( [ 'a', 'b' ] )
    assert res == [ 'obj1', 'obj2' ]
    
    res = db.get( [ 'a', 'd' ] )
    assert res == [ 'obj1' ]

    res = db.get( [ 'a', 'f' ] )
    assert res == [ 'obj2' ]

    res = db.get( [ 'd', 'f' ] )
    assert res == []
    
def test_get_tags_by_tags():
    test_add_tags()
    
    res = db.get_tags( ['a', 'b' ] )
    assert res == [ 'c', 'd', 'e' ]
    
    res = db.get_tags( ['a', 'b', 'd' ] )
    assert res == [ 'e' ]

    res = db.get_tags( ['a', 'b', 'f' ] )
    assert res == [ 'g' ]

    res = db.get_tags( ['a', 'b', 'e', 'f' ] )
    assert res == []

def test_get_tags_by_objs():
    test_add_tags()
    
    res = db.get_tags( objs = [ 'obj1' ] )
    assert res == [ 'a', 'b', 'c', 'd', 'e' ]

    res = db.get_tags( objs = [ 'obj2' ] )
    assert res == [ 'a', 'b', 'c', 'f', 'g' ]

    res = db.get_tags( objs = [ 'obj1', 'obj2' ] )
    assert res == [ 'a', 'b', 'c' ]

def run_test( test_func ):
    print 'Running %s... ' % test_func.__name__,
    
    test_func()
    
    print 'Passed!'

def run_all_tests():
    run_test( test_add_tags )
    
    run_test( test_get_objs_by_tags )
    
    run_test( test_get_tags_by_tags )
    
    run_test( test_get_tags_by_objs )

if __name__ == '__main__':
    run_all_tests()
