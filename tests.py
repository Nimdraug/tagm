#!/usr/bin/env python2
import tagm
import unittest

class TagmTestCase( unittest.TestCase ):
    def setUp( self ):
        self.db = tagm.TagmDB( ':memory:' )

class TestAdd( TagmTestCase ):
    def test_add_single_obj( self ):
        self.assertIsNone( self.db.add( [ 'a' ], [ 'obj1' ] ) )

    def test_add_multiple_obj( self ):
        self.assertIsNone( self.db.add( [ 'a' ], [ 'obj1', 'obj2' ] ) )
    
    def test_add_multiple_tags( self ):
        self.assertIsNone( self.db.add( [ 'a', 'b' ], [ 'obj1' ] ) )
    
    def test_add_multiple_both( self ):
        self.assertIsNone( self.db.add( [ 'a', 'b' ], [ 'obj1', 'obj2' ] ) )
    
    def test_add_subtag( self ):
        self.assertIsNone( self.db.add( [ [ 'a', 'b' ] ], [ 'obj1' ] ) )

class TagmGetTestCase( TagmTestCase ):
    def setUp( self ):
        super( TagmGetTestCase, self ).setUp()
        
        self.db.add( [ 'a' ], [ 'obj1', 'obj2', 'obj3' ] )
        self.db.add( [ 'b' ], [ 'obj2', 'obj3' ] )
        self.db.add( [ 'c' ], [ 'obj3' ] )
        self.db.add( [ [ 'c', 'd' ] ], [ 'obj1' ] )

class TestGetObjsByTags( TagmGetTestCase ):
    def test_get_single_tag( self ):
        self.assertEqual( self.db.get( [ 'b' ] ), [ 'obj2', 'obj3' ] )

    def test_get_multiple_tags( self ):
        self.assertEqual( self.db.get( [ 'a', 'b' ] ), [ 'obj2', 'obj3' ] )
    
    def test_get_subtag( self ):
        self.assertEqual( self.db.get( [ [ 'c', 'd' ] ] ), [ 'obj1' ] )
    
    def test_get_subtag_parent( self ):
        self.assertEqual( self.db.get( [ [ 'c' ] ] ), [ 'obj3' ] )
    
    def test_get_subtag_parent_include_subtags( self ):
        self.assertEqual( self.db.get( [ 'c' ], subtags = True ), [ 'obj3', 'obj1' ] )
    
    def test_get_invalid_tag( self ):
        # TODO: Should this raise an exception? Ie TagNotFoundError
        #       Requires TagmDB.get to not handle TagNotFoundError
        #       Question is, is that desired behavior?
        self.assertEqual( self.db.get( [ 'e' ] ), [] )

class TestGetTagsByTags( TagmGetTestCase ):
    def test_get_single_tag( self ):
        self.assertItemsEqual( self.db.get( [ 'a' ], obj_tags = True ), [ [ 'b' ], [ 'c' ], [ 'c', 'd' ] ] )
    
    def test_get_multiple_tags( self ):
        self.assertItemsEqual( self.db.get( [ 'a', 'b' ], obj_tags = True ), [ [ 'c' ] ] )

    def test_get_subtag( self ):
        self.assertEqual( self.db.get( [ [ 'c', 'd' ] ], obj_tags = True ), [ [ 'a' ] ] )
    
    def test_get_subtag_parent( self ):
        self.assertEqual( self.db.get( [ [ 'c' ] ], obj_tags = True ), [ [ 'a' ], [ 'b' ] ] )
    
    def test_get_subtag_parent_include_subtags( self ):
        self.assertEqual( self.db.get( [ 'c' ], obj_tags = True, subtags = True ), [ [ 'a' ], [ 'b' ], [ 'c', 'd' ] ] )
        
def test_get_tags_by_objs():
    test_add_tags()
    
    res = db.get_obj_tags( [ 'obj1' ] )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ], [ 'd' ], [ 'e' ], [ 'i', 'j' ] ]

    res = db.get_obj_tags( [ 'obj2' ] )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ], [ 'f' ], [ 'g' ], [ 'i' ] ]

    res = db.get_obj_tags( [ 'obj1', 'obj2' ] )
    assert res == [ [ 'a' ], [ 'b' ], [ 'c' ] ]
    
    res = db.get_obj_tags( [] )
    assert res == []

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
    unittest.main()
