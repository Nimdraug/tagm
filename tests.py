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
    
    # TODO: Test for add with find instead of objects, ie:
    # db.add( ['h'], find = [ 'a', 'c' ] )
    # should tag both obj 1 and 2 with h
    
    # TODO: Should it be passed as [ ['i','j'] ] instead..?
    #       Thus leave the delimiter up to downstream?
    db.add( [ [ 'i', 'j' ] ], [ 'obj1' ] )
    db.add( [ 'i' ], [ 'obj2' ] )

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
    
    res = db.get( [ 'a', 'i' ], subtags = True )
    assert res == [ 'obj1', 'obj2' ]
    
    res = db.get( [ 'a', [ 'i', 'j' ] ] )
    assert res == [ 'obj1' ]
    
    res = db.get( [] )
    assert res == [ 'obj1', 'obj2' ]
    
    # TODO: Should this raise an exception? Ie TagNotFoundError
    #       Requires TagmDB.get to not handle TagNotFoundError
    #       Question is, is that desired behavior?
    res = db.get( [ 'h' ] )
    assert res == []
    
def test_get_tags_by_tags():
    test_add_tags()
    
    res = db.get( [ 'a', 'b' ], True )
    assert res == [ [ 'c' ], [ 'd' ], [ 'e' ], [ 'i', 'j' ], [ 'f' ], [ 'g' ], [ 'i' ] ]
    
    res = db.get( ['a', 'b', 'd' ], True )
    assert res == [ [ 'c' ], [ 'e' ], [ 'i', 'j' ] ]

    res = db.get( ['a', 'b', 'f' ], True )
    assert res == [ [ 'c' ], [ 'g' ], [ 'i' ] ]

    res = db.get( ['a', 'b', 'e', 'f' ], True )
    assert res == []
    
    res = db.get( [ 'i' ], True )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ], [ 'f' ], [ 'g' ] ]

    res = db.get( [ 'i' ], True, True )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ], [ 'd' ], [ 'e' ], [ 'i', 'j' ], [ 'f' ], [ 'g' ] ]

def test_get_tags_by_objs():
    test_add_tags()
    
    res = db.get_obj_tags( [ 'obj1' ] )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ], [ 'd' ], [ 'e' ], [ 'i', 'j' ] ]

    res = db.get_obj_tags( [ 'obj2' ] )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ], [ 'f' ], [ 'g' ], [ 'i' ] ]

    res = db.get_obj_tags( [ 'obj1', 'obj2' ] )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ] ]
    
    res = db.get_obj_tags( [] )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ], [ 'd' ], [ 'e' ], [ 'f' ], [ 'g' ], [ 'i', 'j' ], [ 'i' ] ]

    # TODO: Test for non existing objs
    #       Ie:
    # res = db.get_obj_tags( [ 'obj3' ] )
    # assert res == []
    # -- or --
    # check that ObjNotFoundError got raised

def run_test( test_func ):
    print 'Running %s...' % test_func.__name__,
    
    test_func()
    
    print 'Passed!'

def run_all_tests():
    run_test( test_add_tags )
    
    run_test( test_get_objs_by_tags )
    
    run_test( test_get_tags_by_tags )
    
    run_test( test_get_tags_by_objs )

if __name__ == '__main__':
    run_all_tests()
