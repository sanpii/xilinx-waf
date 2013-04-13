#!/usr/bin/env python

# .v -> .prj -> .xst -> .ngc -> .ngd -> .ncd -> -routed.ncd -> .bit

import os, platform
from waflib import Task
from waflib.TaskGen import extension

class verilog(Task.Task):
    color = "BLUE"

    def run(self):
        for source in self.inputs:
            self.outputs[0].write("verilog work %s\n" % source.abspath())

class prj(Task.Task):
    color = "BLUE"

    def run(self):
        source = self.inputs[0].abspath()
        target = os.path.splitext(self.outputs[0].__str__())[0]
        device = self.env.DEVICE

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

class ngc(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_XST} -ifn ${SRC[0].abspath()} -ofn ${TGT[0].abspath()}"

class ngd(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_NGDBUILD} -uc ${UCF} -p ${DEVICE} ${SRC[0].abspath()} ${TGT[0].abspath()}"

class ncd(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_MAP} -p ${DEVICE} -detail -pr off -o ${TGT[0].abspath()} ${SRC[0].abspath()}"

class routed_ncd(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_PAR} ${SRC[0].abspath()} ${TGT[0].abspath()}"

class bitgen(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_BITGEN} -w -g StartUpClk:CClk -g CRC:Enable ${SRC[0].abspath()} ${TGT[0].abspath()}"

@extension(".v")
def verilog_file(self, node):
    try:
        verilog_task = self.verilog_task
    except AttributeError:
        verilog_task = self.verilog_task = self.create_task('verilog')

    verilog_task.inputs.append(node)
    prj_node = self.bld.bldnode.find_or_declare("%s.prj" % self.target)
    verilog_task.outputs.append(prj_node)
    self.source.append(prj_node)

@extension(".prj")
def project_file(self, node):
    xst_node = self.bld.bldnode.find_or_declare("%s.xst" % self.target)
    task = self.create_task("prj", node, xst_node)
    self.source.append(xst_node)

@extension(".xst")
def xst_file(self, node):
    ngc_node = self.bld.bldnode.find_or_declare("%s.ngc" % self.target)
    self.create_task("ngc", node, ngc_node)
    self.source.append(ngc_node)

@extension(".ngc")
def ngc_file(self, node):
    ngd_node = self.bld.bldnode.find_or_declare("%s.ngd" % self.target)
    task = self.create_task("ngd", node, ngd_node)
    self.source.append(ngd_node)

@extension(".ngd")
def ngd_file(self, node):
    ncd_node = self.bld.bldnode.find_or_declare("%s.ncd" % self.target)
    task = self.create_task("ncd", node, ncd_node)
    self.source.append(ncd_node)

@extension(".ncd")
def ncd_file(self, node):
    routed_ncd_node = self.bld.bldnode.find_or_declare("%s-routed.ncd" % self.target)
    self.create_task("routed_ncd", node, routed_ncd_node)
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
        action="store",
        dest="dir",
        default="/opt/Xilinx/14.5/ISE_DS/ISE",
        help="xilinx ise directory"
    )
