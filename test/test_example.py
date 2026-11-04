import pytest

def test_equal_or_not_equal():
    assert 3==3
    assert 3!=2
    assert 4==4
    assert 4!=5


def test_is_instance():
    assert isinstance(3, int)
    assert not isinstance(3, str)

def test_boolean():
    assert True
    assert not False

def test_type():
    assert type(3) == int
    assert type("hello") == str


def test_greater_or_less():
    assert 5 > 3
    assert 3 < 5
    assert not 3 > 5
    assert not 5 < 3


def test_list():
    my_list = [1, 2, 3]
    assert 1 in my_list
    assert 4 not in my_list
    assert len(my_list) == 3
    assert my_list[0] == 1
    assert my_list[-1] == 3
    assert my_list[1:3] == [2, 3]


class Student:
    def __init__(self, firstname, lastname, age, major):
        self.firstname = firstname
        self.lastname = lastname
        self.age = age
        self.major = major

@pytest.fixture
def student():
    return Student("Alice", "Smith", 20, "Computer Science")

def test_student_initialization(student):
    assert student.firstname == "Alice", "Firstname should be Alice"
    assert student.lastname == "Smith", "Lastname should be Smith"
    assert student.age == 20, "Age should be 20"
    assert student.major == "Computer Science", "Major should be Computer Science"
