class Config:
    SECRET_KEY = "supersecretkey"
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:@localhost/hospital"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
