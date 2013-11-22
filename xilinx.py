#!/usr/bin/env python

import os, platform, shutil

from waflib.Build import BuildContext
from waflib import Logs

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

    conf.env["XILINX_DIR"] = conf.options.dir

def configure(conf):
    tools = ["xst", "ngdbuild", "map", "par", "bitgen", "fuse"]

    if conf.options.simtool == "xilinx":
        tools += ["vlogcomp"]
    else:
        conf.env["IVERILOG"] = conf.find_program("iverilog")
        conf.env["VVP"] = conf.find_program("vvp")

    for tool in tools:
        xilinx_find_tool(conf, tool)

def options(opt):
    opt.add_option(
        "--xilinx-dir",
        action = "store",
        dest = "dir",
        default = "/opt/Xilinx/14.5/ISE_DS/ISE",
        help = "xilinx ise directory"
    )
    opt.add_option(
        "--simtool",
        action = "store",
        dest = "simtool",
        default = "xilinx",
        help = "xilinx simulate tool (xilinx or iverilog)"
    )

class XilinxProject(object):
    def __init__(self, ctx, tg):
        self.path = ctx.bldnode
        self.ctx = ctx
        self.name = tg.name
        self.sources = tg.to_nodes(getattr(tg, 'source', []))
        self.tg = tg

        try:
            self.device = tg.device
        except AttributeError:
            self.device = None

        try:
            self.ucf = tg.path.find_resource(tg.ucf)
        except AttributeError:
            self.ucf = None


    def simulate(self):
        if not self.tg.env.XILINX_VLOGCOMP:
            self.simulate_iverilog()
        else:
            self.simulate_xilinx()

    def simulate_xilinx(self):
        shutil.copy(
            "%s/verilog/src/glbl.v" % self.tg.env.XILINX_DIR,
            "%s/glbl.v" % self.path.abspath()
        )
        source = self.path.make_node("glbl.v")
        self.sources.append(source)

        project = self.create_project(self.sources)
        self.vlogcomp(project)
        exe = self.create_exe(project)

    def vlogcomp(self, project):
        Logs.info("=> Running vlogcomp")

        tool = self.tg.env.XILINX_VLOGCOMP

        cmd = "%(tool)s -work isim_temp -intstyle ise -prj %(project)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

    def create_exe(self, project):
        Logs.info("=> Create exe file")

        exe = project.change_ext(".exe")

        tool = self.tg.env.XILINX_FUSE
        source = project.abspath()
        target = exe.abspath()
        name = self.name
        module = "blinkTest"

        cmd = "%(tool)s -incremental -lib unisims_ver -lib unimacro_ver -lib xilinxcorelib_ver -o %(target)s -prj %(source)s %(name)s.%(module)s %(name)s.glbl" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

        return exe

    def simulate_iverilog(self):
        vvp = self.iverelog()
        self.vvp(vvp)

    def iverelog(self):
        Logs.info("=> Running iverilog")

        tool = self.tg.env.IVERILOG
        sources = ''
        for source in self.sources:
            sources += " " + source.abspath()
        project = self.name

        cmd = "%(tool)s -o %(project)s %(sources)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

        return project

    def vvp(self, vvp):
        Logs.info("=> Running vvp")

        tool = self.tg.env.VVP
        cmd = "%(tool)s -n %(vvp)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

    def build(self):
        project = self.create_project(self.sources)
        [ngc, xst] = self.create_xst(project)
        ngc = self.create_ngc(xst, ngc)
        ngd = self.create_ngd(ngc)
        ncd = self.map(ngd)
        routed_ncd = self.places_and_routes(ncd)
        self.bitgen(routed_ncd)

    def create_project(self, sources):
        Logs.info("=> Create project file")

        data = ''
        for source in sources:
            data = data + "verilog %s %s\n" % (self.name, source.abspath())

        project = self.path.make_node(self.name + '.prj')
        project.write(data)

        return project

    def create_xst(self, project):
        Logs.info("=> Create xst file")

        xst = project.change_ext(".xst")
        ngc = xst.change_ext(".ngc")

        source = project.abspath()
        name = self.name
        target = ngc.abspath()
        device = self.device

        xst.write("""run
-ifn %(source)s
-top %(name)s
-ifmt MIXED
-ofn %(target)s
-ofmt NGC
-p %(device)s
-opt_mode Speed
-opt_level 1
""" % locals())

        return [ngc, xst]

    def create_ngc(self, xst, ngc):
        Logs.info("=> Run xst file")

        tool = self.tg.env.XILINX_XST
        source = xst.abspath()

        cmd = "%(tool)s -ifn %(source)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

        return ngc

    def create_ngd(self, ngc):
        Logs.info("=> Run ngdbuild")

        ngd = ngc.change_ext(".ngd")

        tool = self.tg.env.XILINX_NGDBUILD
        ucf = self.ucf.abspath()
        device = self.device
        source = ngc.abspath()
        target = ngd.abspath()

        cmd = "%(tool)s -uc %(ucf)s -p %(device)s %(source)s %(target)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

        return ngd

    def map(self, ngd):
        Logs.info("=> Map")

        ncd = ngd.change_ext(".ncd")

        tool = self.tg.env.XILINX_MAP
        device = self.device
        source = ngd.abspath()
        target = ncd.abspath()

        cmd = "%(tool)s -p %(device)s -detail -pr off -o %(target)s %(source)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

        return ncd

    def places_and_routes(self, ncd):
        Logs.info("=> Places and routes")

        routed_ncd = ncd.change_ext("-routed.ncd")

        tool = self.tg.env.XILINX_PAR
        source = ncd.abspath()
        target = routed_ncd.abspath()

        cmd = "%(tool)s -w %(source)s %(target)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

        return routed_ncd

    def bitgen(self, routed_ncd):
        Logs.info("=> Bitgen")

        bit = routed_ncd.change_ext(".bit", "-routed.ncd")

        tool = self.tg.env.XILINX_BITGEN
        source = routed_ncd.abspath()
        target = bit.abspath()

        cmd = "%(tool)s -w -g StartUpClk:CClk -g CRC:Enable %(source)s %(target)s" % locals()
        self.ctx.exec_command(cmd, cwd=self.path.abspath())

        return bit

class XilinxContext(BuildContext):

    def init(self):
        self.restore()
        if not self.all_envs:
            self.load_envs()
        self.recurse([self.run_dir])

    def collect_projects(self):
        projects = []

        for g in self.groups:
            for tg in g:
                projects.append(XilinxProject(self, tg))

        return projects

# .v -> .prj -> .xst -> .ngc -> .ngd -> .ncd -> -routed.ncd -> .bit
class Synthetize(XilinxContext):
    fun = 'synthetize'

    def execute(self):
        self.init()
        projects = self.collect_projects()
        for project in projects:
            project.build()

# .v -> .prj -> .exe
class Simulate(XilinxContext):
    cmd = 'sim'
    fun = 'simulate'

    def execute(self):
        self.init()
        projects = self.collect_projects()
        for project in projects:
            project.simulate()
