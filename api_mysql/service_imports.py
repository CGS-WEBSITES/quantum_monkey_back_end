from datetime import timedelta
from flask import Flask, jsonify
from flask_restx import Api
from flask_cors import CORS
from sqlalchemy import create_engine
from helper.refresh_token import refresh
from flask_jwt_extended import JWTManager
from config import DATABASE_URI, SECRET_KEY
from sql_alchemy import banco
from bcryptInit import bcrypt
import logging
