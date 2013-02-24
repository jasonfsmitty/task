#!/usr/bin/env python

import sys, os.path, logging, sqlite3

def _dump_table( db, out, table ):
    try:
        out.write( "%s Table:\n" % (table) )
        cursor = db.cursor()
        cursor.execute( "SELECT * FROM %s" % (table) )
        for row in cursor:
            out.write( "\t%s\n" % str(row) )
        out.write( "\n" )
    except sqlite3.Error as e:
        logging.error( "Error dumping table %s: error=%s", table, str(e.args[0]) )

#--------------------------------------------------------------------------
class TaskTable(object):
    def __init__( self, db ):
        self._database = db

    def create_status_table( self ):
        columns = [
            "statusid INTEGER PRIMARY KEY",
            "name TEXT",
            "short TEXT"
        ]
        values =  [
            ( 1, 'Open',      'O' ),
            ( 2, 'Closed',    'C' ),
            ( 3, 'Withdrawn', 'W' )
        ]
        try:
            with self._database.connection() as conn:
                conn.execute( "CREATE TABLE IF NOT EXISTS Status ( %s )" % (','.join(columns)) )
                conn.executemany( "INSERT or IGNORE INTO Status ( statusid, name, short ) VALUES (?,?,?)", values )
        except sqlite3.Error as e:
            logging.error( "Failed to initialize Status table: %s", str( e.args[0] ) )

    def create_task_table( self ):
        columns = [
            "taskid INTEGER PRIMARY KEY AUTOINCREMENT",
            "name TEXT",
            "details TEXT",
            "parent INTEGER",
            "statusid INTEGER",
            "FOREIGN KEY(statusid) REFERENCES Status(statusid)"
        ]
        try:
            with self._database.connection() as conn:
                conn.execute( "CREATE TABLE IF NOT EXISTS Task ( %s )" % (','.join(columns)) )
        except sqlite3.Error as e:
            logging.error( "Failed to initialize Task table: %s", str( e.args[0] ) )

    def create( self ):
        self.create_status_table()
        self.create_task_table()

    def debug( self, out ):
        _dump_table( self._database, out, "Task" )
        _dump_table( self._database, out, "Status" )

    def select( self, columns=["taskid","name","details","parent","statusid"] ):
        try:
            cursor = self._database.cursor()
            cursor.execute( "SELECT %s FROM Task" % (','.join( columns )) )
            return [ dict( zip( columns, row ) ) for row in cursor ]
        except sqlite3.Error as e:
            logging.error( "Error getting tasks: columns=%s error=%s", str(columns), str(e.args[0]) )
            return None

    def insert( self, name, details="", status='O' ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.execute( "INSERT INTO Task ( name, details ) VALUES ( ?, ? )", ( name, details ) )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error( "Failed to insert new task: %s", str( e.args[0] ) )
            return None

    def update( self, taskid, name ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.execute( "UPDATE Task SET name=? WHERE taskid=?", (name, taskid) )
            return True
        except sqlite3.Error as e:
            logging.error( "Failed to update task: %s", str( e.args[0] ) )
            return False

    def delete( self, ids ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.executemany( "DELETE FROM Task WHERE taskid=?", [ (id,) for id in ids ] )
            return True
        except sqlite3.Error as e:
            logging.error( "Failed to delete tasks: ids=%s error=%s", str(ids), str(e.args[0]) )
            return False

    def set_parent( self, taskid, parent ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.execute( "UPDATE Task SET parent=? WHERE taskid=?", (parent, taskid) )
            return True
        except sqlite3.Error as e:
            logging.error( "Failed to set task[%u] as parent to task[%u]", parent, taskid )
            return False

#--------------------------------------------------------------------------
class MessageTable(object):
    def __init__( self, db ):
        self._database = db

    def create( self ):
        columns = [
            'msgid INTEGER PRIMARY KEY AUTOINCREMENT',
            'date DATE',
            'ts TIMESTAMP',
            'text TEXT'
        ]
        try:
            with self._database.connection() as conn:
                conn.execute( "CREATE TABLE IF NOT EXISTS Message ( %s )" % (','.join(columns) ) )
        except sqlite3.Error as e:
            logging.error( "Failed to initialize Message table: %s", str( e.args[0] ) )

    def debug( self, out ):
        _dump_table( self._database, out, "Message" )

    def select( self, columns=[ 'date', 'ts', 'text' ] ):
        try:
            cursor = self._database.cursor()
            cursor.execute( "SELECT %s FROM Message" % (','.join(columns)) )
            return [ dict( zip( columns, row ) ) for row in cursor ]
        except sqlite3.Error as e:
            logging.error( "Error getting messages: colunns=%s error=%s", str(columns), str(e.args[0]) )
            return None

    def insert( self, text ):
        try:
            today = datetime.date.today()
            now = datetime.datetime.now()
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.execute( "INSERT INTO Message ( date, ts, text ) VALUES ( ?, ?, ? )", ( today, now, text ) )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error( "Failed to insert new message: %s", str( e.args[0] ) )
            return None


#--------------------------------------------------------------------------
class Database(object):
    def __init__( self, filename="/home/jasmith/.taskbook.db" ):
        self._filename = filename
        self._connection = sqlite3.connect( self._filename )

        self._tasks = TaskTable( self )
        self._messages = MessageTable( self )

        self.init()

    def debug( self, out ):
        out.write( "DB filename=%s\n\n" % self._filename )
        self._tasks.debug( out )
        self._messages.debug( out )

    def init( self ):
        self._tasks.create()
        self._messages.create()

    def connection( self ):
        return self._connection

    def cursor( self ):
        return self._connection.cursor()

    @property
    def tasks( self ):
        return self._tasks

#--------------------------------------------------------------------------
class Taskbook(object):
    def __init__( self, database ):
        self._database = database
        self._tasks = dict() # { taskid: task }

    def debug( self, out ):
        out.write( "In memory tasks:\n" )
        out.write( "\t%s\n\n" % str(self._tasks) )
        self._database.debug( out )

    def refresh( self ):
        self._tasks = dict()

        raw = self._database.tasks.select()
        for task in raw:
            task['kids'] = []
            self._tasks[ task['taskid'] ] = task

        for task in raw:
            if task['parent']:
                self._tasks[ task['parent'] ]['kids'].append( task['taskid'] )

    def add( self, name, details="" ):
        return self._database.tasks.insert( name=name, details=details )

    def _list( self, task, indent=0 ):
        print "%4i : %s%s" % ( task['taskid'], '  '*indent, task['name'])
        for kid in task['kids']:
            self._list( self._tasks[ kid ], indent+1 )

    def list( self ):
        self.refresh()
        for task in self.select():
            self._list( task )

    def _kids( self, taskid ):
        kids = self._tasks[taskid]['kids']
        for kid in kids:
            kids.extend( self._kids( kid ) )
        return kids

    def delete( self, taskid ):
        self.refresh()
        ids = [ taskid ]
        ids.extend( self._kids( taskid ) )
        return self._database.tasks.delete( ids )

    def update( self, taskid, name ):
        return self._database.tasks.update( taskid, name )

    def move( self, taskid, parent ):
        self.refresh()
        return self._database.tasks.set_parent( taskid, parent )

    def select( self, parentid=None ):
        return [ task for task in self._tasks.itervalues() if task['parent'] == parentid ]

#--------------------------------------------------------------------------
class Notebook(object):
    def __init__( self ):
        self._database = Database()
        self._tasks = Taskbook( self._database )

    def debug( self, out ):
        self._tasks.debug( out )

    @property
    def tasks( self ):
        return self._tasks

#--------------------------------------------------------------------------
def do_list( book, args ):
    book = Notebook()
    book.tasks.list()
    return 0

#--------------------------------------------------------------------------
def do_add( book, args ):
    name = ' '.join( args )
    if len(name) == 0:
        usage( "Missing task name!" )
        return 1

    if not book.tasks.add( name=name ):
        return 1
    book.tasks.list()
    return 0

#--------------------------------------------------------------------------
def do_delete( book, args ):
    for x in args:
        book.tasks.delete( int(x) )
    book.tasks.list()
    return 0

#--------------------------------------------------------------------------
def do_move( book, args ):
    if len(args) < 2:
        usage( "Missing move arguments" )
        return 1

    dest = int( args[-1] )
    for source in args[:-1]:
        if not book.tasks.move( int(source), dest ):
            return 1
    book.tasks.list()
    return 0

#--------------------------------------------------------------------------
def do_edit( book, args ):
    if len(args) < 2:
        usage( "Missing edit arguments" )
        return 1

    if not book.tasks.update( int(args[0]), ' '.join( args[1:] ) ):
        return 1

    book.tasks.list()
    return 0

#--------------------------------------------------------------------------
def do_debug( book, args ):
    book.debug( sys.stdout )
    return 0

#--------------------------------------------------------------------------
COMMANDS = {
    'list'    : do_list,
    'add'     : do_add,
    'del'     : do_delete,
    'delete'  : do_delete,
    'move'    : do_move,
    'mv'      : do_move,
    'edit'    : do_edit,
    'debug'   : do_debug
}

#--------------------------------------------------------------------------
def usage( err=None ):
    if err:
        print "ERROR: ", err
    print "usage: TODO"

#--------------------------------------------------------------------------
def main( args ):
    if len(args) > 0:
        command = args[0]
        args = args[1:]
    else:
        command = "list"

    func = COMMANDS.get( command, None )
    if not func:
        usage( "Unknown command '%s'" % command )
        return 1

    return func( Notebook(), args )

#--------------------------------------------------------------------------
if __name__ == "__main__":
    sys.exit( main( sys.argv[1:] ) )

