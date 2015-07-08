#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Purpose: 
Created: 09.09.2014
Author : Aleksey Bogoslovskyi
"""

import os
import sqlite3

# DATABASE = os.path.join(settings.PROJECT_ROOT, settings.STATIC_ROOT, "crisis.db")
try:
    from django.conf import settings
    DATABASE = os.path.join(settings.PROJECT_ROOT, "static", "crisis.db")
except:
    DATABASE = os.path.join(os.path.realpath(os.path.dirname(__file__)), "../static/crisis.db")


# ALTER TABLE participant ADD COLUMN TRADE_ORDER TEXT DEFAULT '{}';

TABLES = """
CREATE TABLE IF NOT EXISTS USERS(
    UID             TEXT UNIQUE NOT NULL,
    NAME            TEXT NOT NULL,
    CLAN_ID         TEXT
    );

CREATE TABLE IF NOT EXISTS CLANS(
    CLAN_ID         TEXT UNIQUE NOT NULL,
    NAME            TEXT NOT NULL
    );

CREATE TABLE IF NOT EXISTS PARTICIPANT(
    UID             TEXT UNIQUE NOT NULL,
    AUTH            TEXT,
    TYPE            TEXT DEFAULT DYNAMIC,
    DAILY_MERC      TEXT DEFAULT OFF,
    DAILY_SCHEMA    TEXT DEFAULT NULL,
    EVENT_SCHEMA    TEXT DEFAULT NULL,
    GROUP_PLUGIN    TEXT DEFAULT NULL
    );

CREATE TABLE IF NOT EXISTS ARCHIVE(
    UID             TEXT UNIQUE NOT NULL,
    AUTH            TEXT
    );

CREATE TABLE IF NOT EXISTS STATISTICS(
    UID             TEXT UNIQUE NOT NULL,
    NAME            TEXT,
    LAST_RATING     INTEGER DEFAULT 0,
    LAST_CLAN       INTEGER DEFAULT 0,
    LAST_CLAN_WIN   INTEGER DEFAULT 0,
    WEEK_RATING     INTEGER DEFAULT 0,
    WEEK_CLAN       INTEGER DEFAULT 0,
    WEEK_CLAN_WIN   INTEGER DEFAULT 0,
    WEEK_PERCENTAGE REAL DEFAULT 0
    );

CREATE TABLE IF NOT EXISTS PRESENT(
    TYPE            TEXT UNIQUE NOT NULL,
    COUNTER         INTEGER,
    START_POINT     INTEGER,
    FIRST_STEP      INTEGER
    );

CREATE TABLE IF NOT EXISTS ADD_RECIPIENTS(
    UID             TEXT UNIQUE NOT NULL
    );

CREATE TABLE IF NOT EXISTS REGION(
    ID              INTEGER UNIQUE NOT NULL,
    REGION_NAME     TEXT
    );

CREATE TABLE IF NOT EXISTS CITY(
    ID              INTEGER NOT NULL,
    REGION_ID       INTEGER NOT NULL,
    CITY_NAME       TEXT
    )
"""


def dict_factory(cursor, row):
    """ Convert query result from array of tuples to array of dictionary """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DB_API(object):
    def __init__(self):
        self.connection = sqlite3.connect(DATABASE)
        self.connection.row_factory = dict_factory

    def create_tables(self, cursor=None):
        """ Initial tables create """
        if cursor is None:
            cursor = self.connection.cursor()
        for table in TABLES.split(";"):
            cursor.execute(table)
        cursor.close()

    def upsert_data(self, table, data, cursor=None, commit=True):
        """ Update or Insert data
        @table - table name
        @data - new data in dict format. {column_name: new_data_value}
        """
        if data:
            try:
                if cursor is None:
                    cursor = self.connection.cursor()
                fields = ""
                values = ""
                for key, value in data.iteritems():
                    if fields != "":
                        fields += ", "
                        values += ", "
                    fields += str(key)
                    if isinstance(value, unicode) or isinstance(value, str):
                        value = "'%s'" % value
                    if value is None:
                        value = "NULL"
                    values += str(value)
                sql = "INSERT OR REPLACE INTO %s (%s) VALUES (%s)" % (table, fields, values)
                # print sql
                cursor.execute(sql)
                if commit:
                    self.connection.commit()
            except Exception, err:
                print err
            finally:
                if cursor:
                    cursor.close()

    def get_data(self, table, condition="", order="", multiple=False, with_rowid=False, cursor=None):
        """
        Get data
        @table - table name
        @where - where cause in dict format. {column_name: value}
        """
        try:
            if cursor is None:
                cursor = self.connection.cursor()

            if condition:
                condition = "WHERE %s" % condition

            if order:
                order = "ORDER BY %s" % order

            if with_rowid:
                sql = "SELECT rowid, * FROM %s %s %s" % (table, condition, order)
            else:
                sql = "SELECT * FROM %s %s %s" % (table, condition, order)
            cursor.execute(sql)
            data = cursor.fetchall()
            if multiple:
                return data
            else:
                if data:
                    return data[0]
                else:
                    return {}
        except Exception, err:
            print err
        finally:
            if cursor:
                cursor.close()

    def delete_data(self, table, condition="", cursor=None):
        """ Delete all data from table """
        try:
            if cursor is None:
                cursor = self.connection.cursor()
            if condition:
                condition = "WHERE %s" % condition

            print condition
            cursor.execute("DELETE FROM %s %s" % (table, condition))
            self.connection.commit()
        except Exception, err:
            print err
        finally:
            if cursor:
                cursor.close()


if __name__ == '__main__':
    api = DB_API()


"""
insert into statistics (uid) select uid from participant where TYPE=='DYNAMIC';
"""