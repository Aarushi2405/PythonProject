import MySQLdb

def connection() :
	conn = MySQLdb.connect(host = "localhost", user="root", passwd="A@rushi2405", db = "Details")
	c = conn.cursor()
	return c, conn
