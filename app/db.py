from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    Table,
    create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

class Region(Base):
    __tablename__ = "region"
    id = Column(Integer, primary_key=True, autoincrement=True)
    region = Column(String(255), nullable=False)
    destinations = relationship("Destination", back_populates="region")


class Pair(Base):
    __tablename__ = "pair"
    id = Column(Integer, primary_key=True, autoincrement=True)
    destination_pair = Column(String(255), nullable=False)
    destinations = relationship("Destination", back_populates="pair")


class Destination(Base):
    __tablename__ = "destination"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    region_id = Column(Integer, ForeignKey("region.id"), nullable=False)
    pair_id = Column(Integer, ForeignKey("pair.id"), nullable=False)
    region = relationship("Region", back_populates="destinations")
    pair = relationship("Pair", back_populates="destinations")
    locations = relationship("Location", back_populates="destination")


class Location(Base):
    __tablename__ = "location"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    destination_id = Column(Integer, ForeignKey("destination.id"), nullable=False)
    destination = relationship("Destination", back_populates="locations")


class TravelGroup(Base):
    __tablename__ = "travel_group"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)


class TravelTheme(Base):
    __tablename__ = "travel_theme"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)


class LocationGroupTheme(Base):
    __tablename__ = "location_group_theme"
    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    travel_group_id = Column(Integer, ForeignKey("travel_group.id"), nullable=False)
    travel_theme_id = Column(Integer, ForeignKey("travel_theme.id"), nullable=False)
    rating = Column(Float, nullable=False)


class Hotel(Base):
    __tablename__ = "hotel"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=False)
    location_id = Column(Integer, ForeignKey("location.id"), nullable=False)
    star = Column(Integer, nullable=False)
    rating = Column(Float, nullable=False)


class MustTravelActivity(Base):
    __tablename__ = "must_travel_activity"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    destination_id = Column(Integer, ForeignKey("destination.id"), nullable=False)


class RecommendedActivity(Base):
    __tablename__ = "recommended_activity"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    destination_id = Column(Integer, ForeignKey("destination.id"), nullable=False)


class MustActivityGroupTheme(Base):
    __tablename__ = "must_activity_group_theme"
    id = Column(Integer, primary_key=True, autoincrement=True)
    must_travel_activity_id = Column(
        Integer, ForeignKey("must_travel_activity.id"), nullable=False
    )
    travel_group_id = Column(Integer, ForeignKey("travel_group.id"), nullable=False)
    travel_theme_id = Column(Integer, ForeignKey("travel_theme.id"), nullable=False)
    rating = Column(Float, nullable=False)


class RecommendActivityGroupTheme(Base):
    __tablename__ = "recommend_activity_group_theme"
    id = Column(Integer, primary_key=True, autoincrement=True)
    recommend_activity_id = Column(
        Integer, ForeignKey("recommended_activity.id"), nullable=False
    )
    travel_group_id = Column(Integer, ForeignKey("travel_group.id"), nullable=False)
    travel_theme_id = Column(Integer, ForeignKey("travel_theme.id"), nullable=False)
    rating = Column(Float, nullable=False)
