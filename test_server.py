import pytest
from av import VideoFrame
from server import BouncingBall, computeError

@pytest.fixture
def ball():
    return BouncingBall()

def test_Ball_CrossingBound(ball):
    bound = ball.width 
    radius = ball.r
    assert(ball.isCrossingBound(-1,bound) == True)
    assert(ball.isCrossingBound( 0,bound) == True)
    assert(ball.isCrossingBound( 1+radius,bound) == False)
    assert(ball.isCrossingBound( bound,bound) == True)
    assert(ball.isCrossingBound( bound+1,bound) == True)

def test_Ball_move(ball):
    initial_coords = ball.coords.copy()
    ball.move()
    assert(initial_coords != ball.coords)

def test_compute_error():
    coords = [100, 100]
    actual = [101, 101]
    assert(computeError(coords, actual) == (1,1))