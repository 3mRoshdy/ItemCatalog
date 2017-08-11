from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Category, Base, Item, User

engine = create_engine('sqlite:///categorywithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# SnowBoarding Catalouge
category1 = Category(user_id=1, name="SnowBoarding")

session.add(category1)
session.commit()

item1 = Item(user_id=1, name="Snow Board", description="A board that suits the skiing in winters",
                     category=category1)

session.add(item1)
session.commit()


item2 = Item(user_id=1, name="Ice Goggles", description="Protective goggles for the eye at skiing",
                     category=category1)

session.add(item2)
session.commit()


# Soccer Catalouge
category2 = Category(user_id=1, name="Soccer")

session.add(category2)
session.commit()


item1 = Item(user_id=1, name="Soccer Ball", description="SoccerBall for scorring goals",
                     category=category2)

session.add(item2)
session.commit()

item2 = Item(user_id=1, name="Soccer Kit",
                     description="The Kit that is wear for playing for a given team",
                      category=category2)

session.add(item2)
session.commit()


# Baseball Catalouge
category3 = Category(user_id=1, name="Baseball")

session.add(category3)
session.commit()


item1 = Item(user_id=1, name="Baseball Bat", description="A Bat for sending the ball to home run",
                     category=category3)

session.add(item1)
session.commit()

items = Item(user_id=1, name="Baseball Gloves", description="Gloves for easing the handeling of the bat",
                     category=category3)

session.add(item2)
session.commit()

item3 = Item(user_id=1, name="Baseball hat", description="A fine hat for playing Baseball",
                     category=category3)

session.add(item3)
session.commit()


print "added menu items!"
