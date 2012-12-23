#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wx

try:
    import treemixin
except ImportError:
    from wx.lib.mixins import treemixin

#--------------------------------------------------------------
class TaskTreeMixin(treemixin.VirtualTree, treemixin.DragAndDrop,
            treemixin.ExpansionState):

    def __init__( self, *args, **kwargs ):
        super(TaskTreeMixin, self).__init__( *args, **kwargs )
        self.RefreshItems()
        self.CreateImageList()

    def CreateImageList(self):
        size=(16,16)
        self.imageList = wx.ImageList( *size )
        for art in wx.ART_FOLDER, wx.ART_FILE_OPEN, wx.ART_NORMAL_FILE:
            self.imageList.Add( wx.ArtProvider.GetBitmap( art, wx.ART_OTHER, size ) )
        self.AssignImageList( self.imageList )

    def OnGetItemFont(self, indices):
        if len(indices) < 4:
            return wx.SMALL_FONT
        else:
            return super(TaskTreeMixin,self).OnGetItemFont(indices)

    def OnGetItemImage(self, indices, which):
        if which in [wx.TreeItemIcon_Normal, wx.TreeItemIcon_Selected]:
            if len(indices) < 4:
                return 0
            else:
                return 2
        else:
            return 1

    def OnGetItemText(self, indices):
        text="blah " + str(indices)
        print "OnGetItemText[", indices, "]=", text
        return text

    def OnGetChildrenCount(self, indices):
        count = 4 - len(indices)
        print "GetChidrenCount[", indices, "]=", count
        return count

    def OnDrop(self, target, item):
        print "OnDrop target=", target, " item=", item

#--------------------------------------------------------------
class TaskTree(TaskTreeMixin, wx.TreeCtrl):
    pass

#--------------------------------------------------------------
class TaskOverviewPanel(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__( self, *args, **kwds )
        self.newTaskText = wx.TextCtrl(self, -1, "", style=wx.TE_PROCESS_ENTER)
        self.newTaskText.Bind( wx.EVT_TEXT_ENTER, self.OnTaskEnter )

        self.taskTree = TaskTree(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.taskTree, 1, wx.EXPAND, 0)
        sizer.Add(self.newTaskText, 0, wx.EXPAND, 0)
        self.SetSizer(sizer)

        self.newTaskText.SetFocus()

    def OnFocus(self, event):
        self.newTaskText.SetFocus()

    def OnTaskEnter(self, event):
        text = self.newTaskText.GetValue().strip()
        if len(text):
            print "Add Task: %s" % (text)
        self.newTaskText.Clear()
        self.RefreshItems()

    def RefreshItems(self):
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
        wx.Frame.__init__(self, *args, **kwds)
        self.notebook = wx.Notebook(self, -1, style=0)

        self.notebook_pane_1 = TaskOverviewPanel(self.notebook, -1)
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
    frame = MyFrame2(None,-1,"")
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()