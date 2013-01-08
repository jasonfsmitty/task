#!/usr/bin/env python

import sys, os.path, logging, sqlite3

#--------------------------------------------------------------------------
class TaskTable(object):
    def __init__( self, db ):
        self._database = db

    def create( self ):
        columns = [
            "taskid INTEGER PRIMARY KEY AUTOINCREMENT",
            "name TEXT",
            "description TEXT",
            "parent INTEGER"
        ]
        try:
            with self._database.connection() as conn:
                conn.execute( "CREATE TABLE IF NOT EXISTS Tasks ( %s )" % (','.join(columns)) )
        except sqlite3.Error as e:
            logging.error( "Failed to initialize Task table: %s", str( e.args[0] ) )

    def select( self, columns=["taskid","name","description","parent"] ):
        try:
            cursor = self._database.cursor()
            cursor.execute( "SELECT %s FROM Tasks" % (','.join( columns )) )
            return [ dict( zip( columns, row ) ) for row in cursor ]
        except sqlite3.Error as e:
            logging.error( "Error getting tasks: columns=%s error=%s", str(columns), str(e.args[0]) )
            return None

    def insert( self, name, description="" ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.execute( "INSERT INTO Tasks ( name, description ) VALUES ( ?, ? )", ( name, description ) )
            return cursor.lastrowid
        except sqlite3.Error as e:
            logging.error( "Failed to insert new task: %s", str( e.args[0] ) )
            return None

    def update( self, taskid, name ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.execute( "UPDATE Tasks SET name=? WHERE taskid=?", (name, taskid) )
            return True
        except sqlite3.Error as e:
            logging.error( "Failed to update task: %s", str( e.args[0] ) )
            return False

    def delete( self, ids ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.executemany( "DELETE FROM Tasks WHERE taskid=?", [ (id,) for id in ids ] )
            return True
        except sqlite3.Error as e:
            logging.error( "Failed to delete tasks: ids=%s error=%s", str(ids), str(e.args[0]) )
            return False

    def set_parent( self, taskid, parent ):
        try:
            with self._database.connection() as conn:
                cursor = conn.cursor()
                cursor.execute( "UPDATE Tasks SET parent=? WHERE taskid=?", (parent, taskid) )
            return True
        except sqlite3.Error as e:
            logging.error( "Failed to set task[%u] as parent to task[%u]", parent, taskid )
            return False

#--------------------------------------------------------------------------
class Database(object):
    def __init__( self, filename="/home/jasmith/.taskbook.db" ):
        self._filename = filename
        self._connection = sqlite3.connect( self._filename )

        self._tasks = TaskTable( self )
        self.init()

    def init( self ):
        self._tasks.create()

    def connection( self ):
        return self._connection

    def cursor( self ):
        return self._connection.cursor()

    @property
    def tasks( self ):
        return self._tasks

#--------------------------------------------------------------------------
class Notebook(object):
    def __init__( self ):
        self._database = Database()
        self._tasks = dict() # { taskid: task }

    def refresh( self ):
        self._tasks = dict()

        raw = self._database.tasks.select()
        for task in raw:
            task['kids'] = []
            self._tasks[ task['taskid'] ] = task

        for task in raw:
            if task['parent']:
                self._tasks[ task['parent'] ]['kids'].append( task['taskid'] )

    def add( self, name, description="" ):
        return self._database.tasks.insert( name=name, description=description )

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
def do_list( book, args ):
    book = Notebook()
    book.list()
    return 0

#--------------------------------------------------------------------------
def do_add( book, args ):
    name = ' '.join( args )
    if len(name) == 0:
        usage( "Missing task name!" )
        return 1

    if not book.add( name=name ):
        return 1
    book.list()
    return 0

#--------------------------------------------------------------------------
def do_delete( book, args ):
    for x in args:
        book.delete( int(x) )
    book.list()
    return 0

#--------------------------------------------------------------------------
def do_move( book, args ):
    if len(args) < 2:
        usage( "Missing move arguments" )
        return 1

    dest = int( args[-1] )
    for source in args[:-1]:
        if not book.move( int(source), dest ):
            return 1
    book.list()
    return 0

#--------------------------------------------------------------------------
def do_edit( book, args ):
    if len(args) < 2:
        usage( "Missing edit arguments" )
        return 1

    if not book.update( int(args[0]), ' '.join( args[1:] ) ):
        return 1

    book.list()
    return 0    
#--------------------------------------------------------------------------
COMMANDS = {
    'list'    : do_list,
    'add'     : do_add,
    'del'     : do_delete,
    'delete'  : do_delete,
    'move'    : do_move,
    'mv'      : do_move,
    'edit'    : do_edit
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

