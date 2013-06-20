#!/usr/bin/env python

# .v -> .prj -> .xst -> .ngc -> .ngd -> .ncd -> -routed.ncd -> .bit

import os, platform
from waflib import Task
from waflib.TaskGen import extension

class create_project(Task.Task):
    color = "BLUE"

    def run(self):
        output = ""
        for source in self.inputs:
            output = output + "verilog work %s\n" % source.abspath()
        self.outputs[0].write(output)

class create_xst(Task.Task):
    color = "BLUE"

    def run(self):
        source = self.inputs[0].abspath()
        target = os.path.splitext(self.outputs[0].__str__())[0]
        device = self.device

        self.outputs[0].write("""run
-ifn %(source)s
-top %(target)s
-ifmt MIXED
-ofn %(target)s
-ofmt NGC
-p %(device)s
-opt_mode Speed
-opt_level 1
""" % locals())

class run_xst(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_XST} -ifn ${SRC[0].abspath()}"

class ngdbuild(Task.Task):
    color = "BLUE"

    def run(self):
        tool = self.env.XILINX_NGDBUILD
        ucf = self.ucf.abspath()
        device = self.device
        src = self.inputs[0].abspath()
        tgt = self.outputs[0].abspath()

        cmd = "%(tool)s -uc %(ucf)s -p %(device)s %(src)s %(tgt)s" % locals()
        self.exec_command(cmd)

class map(Task.Task):
    color = "BLUE"

    def run(self):
        tool = self.env.XILINX_MAP
        device = self.device
        src = self.inputs[0].abspath()
        tgt = self.outputs[0].abspath()

        cmd = "%(tool)s -p %(device)s -detail -pr off -o %(tgt)s %(src)s" % locals()
        self.exec_command(cmd)

class places_and_routes(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_PAR} -w ${SRC[0].abspath()} ${TGT[0].abspath()}"

class bitgen(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_BITGEN} -w -g StartUpClk:CClk -g CRC:Enable ${SRC[0].abspath()} ${TGT[0].abspath()}"

@extension(".v")
def verilog_file(self, node):
    try:
        task = self.create_project_task
    except AttributeError:
        task = self.create_project_task = self.create_task("create_project")

    task.inputs.append(node)
    prj_node = self.bld.bldnode.find_or_declare("%s.prj" % self.target)
    task.outputs.append(prj_node)
    self.source.append(prj_node)

@extension(".prj")
def project_file(self, node):
    xst_node = self.bld.bldnode.find_or_declare("%s.xst" % self.target)
    task = self.create_task("create_xst", node, xst_node)
    task.device = self.device
    self.source.append(xst_node)

@extension(".xst")
def xst_file(self, node):
    ngc_node = self.bld.bldnode.find_or_declare("%s.ngc" % self.target)
    self.create_task("run_xst", node, ngc_node)
    self.source.append(ngc_node)

@extension(".ngc")
def ngc_file(self, node):
    ngd_node = self.bld.bldnode.find_or_declare("%s.ngd" % self.target)
    task = self.create_task("ngdbuild", node, ngd_node)
    task.ucf = self.path.find_or_declare(self.ucf)
    task.device = self.device
    self.source.append(ngd_node)

@extension(".ngd")
def ngd_file(self, node):
    ncd_node = self.bld.bldnode.find_or_declare("%s.ncd" % self.target)
    task = self.create_task("map", node, ncd_node)
    task.device = self.device
    self.source.append(ncd_node)

@extension(".ncd")
def ncd_file(self, node):
    routed_ncd_node = self.bld.bldnode.find_or_declare("%s-routed.ncd" % self.target)
    self.create_task("places_and_routes", node, routed_ncd_node)
    self.source.append(routed_ncd_node)

@extension("-routed.ncd")
def routed_ncd_file(self, node):
    bit_node = self.bld.bldnode.find_or_declare("%s.bit" % self.target)
    self.create_task("bitgen", node, bit_node)
    self.source.append(bit_node)

@extension(".bit")
def bit_file(self, node):
    pass

def xilinx_find_tool(conf, name):
    if platform.machine() == "x86_64":
        xilinx_dir = "%s/bin/lin64" % conf.options.dir
    else:
        xilinx_dir = "%s/bin/lin" % conf.options.dir

    key = "XILINX_%s" % name.upper()
    tool = conf.find_program(
        name,
        var = key,
        path_list = xilinx_dir,
    )
    conf.env[key] = tool

def configure(conf):
    for tool in ["xst", "ngdbuild", "map", "par", "bitgen"]:
        xilinx_find_tool(conf, tool)

def options(opt):
    opt.add_option(
        "--xilinx-dir",
        action = "store",
        dest = "dir",
        default = "/opt/Xilinx/14.5/ISE_DS/ISE",
        help = "xilinx ise directory"
    )
