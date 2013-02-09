#!/usr/bin/env python
# -*- coding: utf-8 -*-

import task
import wx

try:
    import treemixin
except ImportError:
    from wx.lib.mixins import treemixin

#--------------------------------------------------------------
class TaskModel(object):
    def __init__(self, taskbook):
        self._taskbook = taskbook

    def GetItem(self, indices):
        tasks = self._taskbook.select()
        task = { 'name': 'Hidden root', 'kids': tasks, 'taskid': 0, 'parent': None }
        for i in indices:
            task = tasks[i]
            tasks =self._taskbook.select( parentid=task['taskid'] )
        return task

    def GetText(self, indices):
        return self.GetItem( indices )['name']

    def GetChildrenCount(self, indices):
        return len( self.GetItem( indices )['kids'] )

    def GetItemId(self, indices):
        task = self.GetItem( indices )
        return task['taskid']

    def Move(self, source, dest):
        self._taskbook.move( source, dest )

    def Edit(self, indices, text):
        taskid = self.GetItemId( indices )
        self._taskbook.update( taskid, text )

    def Delete(self, indices):
        taskid = self.GetItemId( indices )
        self._taskbook.delete( taskid )

#--------------------------------------------------------------
class TaskTree(treemixin.VirtualTree, treemixin.DragAndDrop,
            treemixin.ExpansionState, wx.TreeCtrl):

    def __init__( self, *args, **kwargs ):
        self.taskbook = kwargs.pop("taskbook")
        super(TaskTree, self).__init__( *args, **kwargs )
        self.model = TaskModel( self.taskbook )
        self.RefreshItems()
        self.CreateImageList()

        self.MenuEditId = wx.NewId()
        self.Bind( wx.EVT_MENU, self.OnMenuEdit, id=self.MenuEditId )

        self.MenuDeleteId = wx.NewId()
        self.Bind( wx.EVT_MENU, self.OnMenuDelete, id=self.MenuDeleteId )

        self.Bind( wx.EVT_TREE_END_LABEL_EDIT, self.OnEndEdit, self )
        self.Bind( wx.EVT_TREE_ITEM_MENU, self.OnContextMenu )

    def CreateImageList(self):
        size=(16,16)
        self.imageList = wx.ImageList( *size )
        for art in wx.ART_FOLDER, wx.ART_FILE_OPEN, wx.ART_NORMAL_FILE:
            self.imageList.Add( wx.ArtProvider.GetBitmap( art, wx.ART_OTHER, size ) )
        self.AssignImageList( self.imageList )

    def OnGetItemImage(self, indices, which):
        if which in [wx.TreeItemIcon_Normal, wx.TreeItemIcon_Selected]:
            if self.model.GetChildrenCount(indices) > 0:
                return 0
            else:
                return 2
        else:
            return 1

    def OnGetItemText( self, indices ):
        return self.model.GetText( indices )

    def OnGetChildrenCount(self, indices):
        return self.model.GetChildrenCount( indices )

    def OnDrop(self, target, item):
        itemId   = self.model.GetItemId( self.GetIndexOfItem( item ) )
        targetId = self.model.GetItemId( self.GetIndexOfItem( target ) )
        self.model.Move( itemId, targetId )
        self.GetParent().RefreshItems()

    def OnEndEdit(self, event):
        self.OnEdit( event.GetItem(), event.GetLabel() )
        self.GetParent().RefreshItems()
        event.Veto()

    def OnRightUp(self, event):
        pt = event.GetPosition()
        item, flags = self.HitTest( pt )
        if item:
            self.EditLabel( item )

    def OnEdit(self, item, text ):
        if text and len(text) > 0:
            indices = self.GetIndexOfItem( item )
            self.model.Edit( indices, text )

    def OnContextMenu( self, event ):
        item = event.GetItem()
        if item:
            if True:
                menu = wx.Menu()
                menu.Append( self.MenuEditId, "Edit" )
                menu.Append( self.MenuDeleteId, "Delete" )
                self.PopupMenu( menu )
                menu.Destroy()
            else:
                self.EditLabel( item )
        event.Skip()

    def OnMenuEdit( self, event ):
        item = self.GetSelection()
        self.EditLabel( item )

    def OnMenuDelete( self, event ):
        parent = self
        question = "Really delete?"
        caption = "Confirmation"
        dialog = wx.MessageDialog( parent, question, caption, wx.YES_NO | wx.ICON_QUESTION )
        confirmed = ( dialog.ShowModal() == wx.ID_YES )
        dialog.Destroy()

        if confirmed:
            item = self.GetSelection()
            indices = self.GetIndexOfItem( item )
            self.model.Delete( indices )
            self.GetParent().RefreshItems()

#--------------------------------------------------------------
class TaskOverviewPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        self.taskbook = kwds.pop('taskbook')
        wx.Panel.__init__( self, *args, **kwds )

        self.newTaskText = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER)
        self.newTaskText.Bind( wx.EVT_TEXT_ENTER, self.OnTaskEnter )

        self.taskTree = TaskTree(self, taskbook=self.taskbook)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.newTaskText, 0, wx.EXPAND, 0)
        sizer.Add(self.taskTree, 1, wx.EXPAND, 0)
        self.SetSizer(sizer)

        self.newTaskText.SetFocus()

    def OnFocus(self, event):
        self.newTaskText.SetFocus()

    def OnTaskEnter(self, event):
        text = self.newTaskText.GetValue().strip()
        if len(text):
            self.taskbook.add( text )
        self.newTaskText.Clear()
        self.RefreshItems()

    def RefreshItems(self):
        self.taskbook.refresh()
        self.taskTree.RefreshItems()
        self.taskTree.UnselectAll() 
#--------------------------------------------------------------
class MessagePanel(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__( self, *args, **kwds )
        # TODO

#--------------------------------------------------------------
class MyFrame2(wx.Frame):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        self.taskbook = kwds.pop('taskbook')
        wx.Frame.__init__(self, *args, **kwds)
        self.notebook = wx.Notebook(self, -1, style=0)

        self.notebook_pane_1 = TaskOverviewPanel(self.notebook, -1, taskbook=self.taskbook)
        self.notebook_pane_2 = MessagePanel(self.notebook, -1)

        self.SetTitle("Tasks")
        self.__do_layout()

    def __do_layout(self):
        self.notebook.AddPage(self.notebook_pane_1, "Tasks")
        self.notebook.AddPage(self.notebook_pane_2, "Log")

        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(self.notebook, 1, wx.EXPAND, 0)
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()


#--------------------------------------------------------------
if __name__ == "__main__":
    app = wx.PySimpleApp(0)
    wx.InitAllImageHandlers()
    database = task.Database()
    taskbook = task.Taskbook( database )
    taskbook.refresh()
    frame = MyFrame2(None,-1,"",taskbook=taskbook)
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
