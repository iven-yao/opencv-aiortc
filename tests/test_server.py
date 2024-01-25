from src.server import BouncingBall

def test_Ball_CrossingBound():
    ball = BouncingBall()
    
    bound = ball.width 
    radius = ball.r
    assert(ball.isCrossingBound(-1,bound) == True)
    assert(ball.isCrossingBound( 0,bound) == True)
    assert(ball.isCrossingBound( 1+radius,bound) == False)
    assert(ball.isCrossingBound( bound,bound) == True)
    assert(ball.isCrossingBound( bound+1,bound) == True)

def test_Ball_move():
    ball = BouncingBall()

    x = ball.x
    y = ball.y

    for i in range(100):
        ball.move()
        dx = ball.dx
        dy = ball.dy
        x = x + dx
        y = y + dy
        assert(x == ball.x)
        assert(y == ball.y)