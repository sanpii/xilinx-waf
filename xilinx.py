#!/usr/bin/env python

import os
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

class ngc(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_XST} -ifn ${SRC} -ofn ${TGT} > ngc.log"

class ngd(Task.Task):
    color = "BLUE"

    def run(self):
        bld = self.generator.bld
        cmd = "%s -uc %s -p %s %s %s > ngd.log" % (
            self.env.XILINX_NGDBUILD,
            os.path.join(bld.srcnode.bldpath(), self.ucf),
            self.device,
            self.inputs[0].abspath(),
            self.outputs[0].abspath(),
        )
        return self.exec_command(cmd)

class ncd(Task.Task):
    color = "BLUE"

    def run(self):
        bld = self.generator.bld

        tmp = self.outputs[0].abspath().replace('.ncd', '_map.ncd')
        cmd = "%s -p %s -detail -pr off -o %s %s > map.log" % (
            self.env.XILINX_MAP,
            self.device,
            tmp,
            self.inputs[0].abspath(),
        )
        self.exec_command(cmd)

        cmd = "%s -w %s %s > par.log" % (
            self.env.XILINX_PAR,
            tmp,
            self.outputs[0].abspath(),
        )
        return self.exec_command(cmd)

class bitgen(Task.Task):
    color = "BLUE"
    run_str = "${XILINX_BITGEN} -w -g StartUpClk:CClk -g CRC:Enable ${SRC} ${TGT} > bitgen.log"

@extension(".v")
def verilog_file(self, node):
    try:
        verilog_task = self.verilog_task
    except AttributeError:
        verilog_task = self.verilog_task = self.create_task('verilog')

    verilog_task.inputs.append(node)
    prj_node = self.path.find_or_declare(("%s.prj" % self.target))
    verilog_task.outputs.append(prj_node)
    self.source.append(prj_node)

@extension(".prj")
def project_file(self, node):
    xst_node = node.change_ext(".xst")
    task = self.create_task("prj", node, xst_node)
    task.device = self.device
    self.source.append(xst_node)

@extension(".xst")
def xst_file(self, node):
    ngc_node = node.change_ext(".ngc")
    self.create_task("ngc", node, ngc_node)
    self.source.append(ngc_node)


@extension(".ngc")
def ngc_file(self, node):
    ngd_node = node.change_ext(".ngd")
    task = self.create_task("ngd", node, ngd_node)
    task.ucf = self.ucf
    task.device = self.device
    self.source.append(ngd_node)

@extension(".ngd")
def ngd_file(self, node):
    ncd_node = node.change_ext(".ncd")
    task = self.create_task("ncd", node, ncd_node)
    task.device = self.device
    self.source.append(ncd_node)

@extension(".ncd")
def ncd_file(self, node):
    bit_node = node.change_ext(".bit")
    self.create_task("bitgen", node, bit_node)
    self.source.append(bit_node)

@extension(".bit")
def bit_file(self, node):
    pass

def xilinx_find_tool(conf, name):
    XILINX_ISE_BIN = "%s/bin/lin64" % conf.options.dir

    key = "XILINX_%s" % name.upper()
    tool = conf.find_program(
        name,
        var = key,
        path_list = XILINX_ISE_BIN,
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
