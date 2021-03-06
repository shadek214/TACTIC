#########################################################
#
# Copyright (c) 2005-2008, Southpaw Technology
#                     All Rights Reserved
#
# PROPRIETARY INFORMATION.  This software is proprietary to
# Southpaw Technology, and is not to be reproduced, transmitted,
# or disclosed in any way without written permission.
#
#
#

__all__ = ['MayaException', 'Maya']


import sys, types, re, os

from tactic_client_lib.application.common import AppException, Application

class MayaException(AppException):
    pass



class Maya(Application):
    '''encapsulates the pymaya plugin and its functionality.  It also provides
    a possbility to created a distributed maya server that will not be
    run on the web server'''

    APPNAME = "maya"

    def __init__(self):
        self.name = "maya"

        try:
            import maya
        except:
            print("WARNING: module MayaApplication requires 'maya' module")

        import maya.standalone
        maya.standalone.initialize( name='python' )
        import maya.cmds, maya.mel



    def mel(self, cmd, verbose=None):
        '''Excecute a mel command'''
        import maya
        return maya.mel.eval(cmd)


    # Common maya operations

    #
    # Node functions
    #
    def node_exists(self, node_name):
        node = self.mel("ls %s" % node_name)
        if node == None:
            return False
        else:
            return True



    def add_node(self, node_name, type="transform", unique=False):
        '''creates new node with the given name

        @params:
        node_name: name of the node to be created
        type: type of node to be created
        unique: boolean determining whether this node is to be unique.  If a
            node of this name already exists, then done create it

        @return:
        string: name of the node actually created
        '''
        if unique and self.node_exists(node_name):
            return node_name
            
        return self.mel("createNode -n %s %s" % (node_name, type) )




    def get_nodes_by_name(self, pattern):
        '''get all the nodes that match the given pattern

        @params
        pattern: pattern of the node name

        @return
        list: all of the node names matching the pattern
        '''
        nodes = self.mel('ls "%s"' % pattern)
        if not nodes:
            return []
        else:
            return nodes


    #
    # Attribute functions
    #
    def add_attr(self, node_name, attribute, type="long"):
        '''add an attribute to a given node

        @params
        node_name: name of the node to add the attribute to
        attribute: name of the attribute to be created
        type: for apps that have type attributes, set the type of the attribute

        @return
        None
        '''
        # do nothing if it already exists
        if self.attr_exists(node_name, attribute):
            return
        if type == "string":
            return self.mel('addAttr -ln "%s" -dt "string" %s' % (attribute, node_name) )
        else:
            return self.mel('addAttr -ln "%s" -at "long" %s' % (attribute, node_name) )


    def attr_exists(self, node_name, attribute):
        '''determines whether an attribute exists on a give node name

        @params
        node_name: name of the node that will be queried
        attribute: name of the attribute that wll be queried

        @return
        boolean: True if attribute exists, False if it does not.
        '''
        # don't bother being verbose with this one
        return self.mel("attributeExists %s %s" % (attribute, node_name), verbose=False )



    def get_attr(self, node_name, attribute):
        '''get the attribute value for a give node

        node_name: name of the node that will be queried
        attribute: name of the attribute that wll be queried

        @return
        string: value of attribute
        '''
        if not self.attr_exists(node_name, attribute):
            return ""
        value = self.mel("getAttr %s.%s" % (node_name, attribute) )
        # never return None for an attr
        if value == None:
            return ""
        else:
            return value




    def get_attr_type(self, node, attribute):
        ''' get the attribute type e.g. int, string, double '''
        if not self.attr_exists(node, attribute):
            return ""
        value = self.mel("getAttr -type %s.%s" % (node, attribute) )
        # never return None for an attr
        if not value:
            return ""
        else:
            return value



    def get_all_attrs(self, node):
        keyable = self.mel("listAttr -keyable %s" % node )
        user_defined = self.mel("listAttr -userDefined %s" % node)
        attrs = []
        attrs.extend(keyable)
        if user_defined:
            attrs.extend(user_defined)
        return attrs



    def get_attr_default(self, node, attr):
         return self.mel("attributeQuery -node %s -listDefault %s" % \
            (node, attr) )




    def set_attr(self, node, attr, value, attr_type=""):
        if attr_type == "string":
            self.mel('setAttr %s.%s -type "string" "%s"' % (node,attr,value))
        else:
            '''attr_type is optional for numeric value'''
            self.mel('setAttr %s.%s %s' % (node,attr,value))


    #
    # File operations
    #
    def load(self, path):
        '''loads the given path into session

        @params
        path: the path of the file to load

        @return
        string: the path that was loaded
        '''
        if path.endswith(".ma"):
            self.mel('file -f -options "v=0"  -typ "mayaAscii" -o "%s"' % path)
        else:
            self.mel('file -f -options "v=0"  -typ "mayaBinary" -o "%s"' % path)
        return path



    def save(self, path, file_type=None):
        '''Save the current session to a file

        @params
        path: the full path of the file to be save
        file_type: either "mayaAscii" or "mayaBinary" are supported

        return
        string: the actuall path created
        '''

        if not file_type:
            file_type="mayaAscii"

        if file_type == "mayaAscii" and not path.endswith(".ma"):
            path, ext = os.path.splitext(path)
            path = "%s.ma" % path
        elif file_type == "mayaBinary" and not path.endswith(".mb"):
            path, ext = os.path.splitext(path)
            path = "%s.mb" % path

        # remove the path, if it exists, before saving
        if os.path.exists(path):
            os.unlink(path)

        self.rename(path)
        created_path = self.mel('file -force -save -type %s' % file_type)

        if not os.path.exists(created_path):
            raise MayaException("Could not save to [%s]" % created_path)

        return created_path


    def rename(self, path):
        '''rename the file so that "save" will go to that directory
       
        @params
        path: the path to rename the file to

        @return
        None
        '''
        if path.endswith("/") or path.endswith("\\"):
            path = "%suntitled.ma" % path
        elif not path:
            path = "untitled.ma"
        #elif not path.endswith(".ma"):
        #    path = "%s.ma" % path

        self.mel('file -rename "%s"' % path)
        if path.endswith(".ma"):
            self.mel('file -type "mayaAscii"')
        elif path.endswith(".mb"):
            self.mel('file -type "mayaBinary"')





