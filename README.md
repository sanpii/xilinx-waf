# Xilinx feature for Waf

Use [waf](https://code.google.com/p/waf/) for compile xilinx verilog sources.

## Installation

Copy xilinx.py in your source directory or use git submodule:

    $ git submodule add git://github.com/sanpii/xilinx-waf.git

## Usage

Create ``wscript``:

    #!/usr/bin/env python

    import os

    def option(opt):
        opt.load("xilinx", tooldir = "xilinx-waf")

    def configure(conf):
        conf.load("xilinx", tooldir = "xilinx-waf")

    def build(bld):
        bld(
            target = "blink",
            source = "src/main.v",
            ucf = "src/papilio.ucf",
            device = "xc3s500e-4-vq100",
        )

Configure:

    $ ./waf configure
    Setting top to                           : /home/sanpi/projects/fpga/waf
    Setting out to                           : /home/sanpi/projects/fpga/waf/build
    Checking for program xst                 : /opt/Xilinx/14.5/ISE_DS/ISE/bin/lin64/xst
    Checking for program ngdbuild            : /opt/Xilinx/14.5/ISE_DS/ISE/bin/lin64/ngdbuild
    Checking for program map                 : /opt/Xilinx/14.5/ISE_DS/ISE/bin/lin64/map
    Checking for program par                 : /opt/Xilinx/14.5/ISE_DS/ISE/bin/lin64/par
    Checking for program bitgen              : /opt/Xilinx/14.5/ISE_DS/ISE/bin/lin64/bitgen
    'configure' finished successfully (0.004s)

And run:

    $ ./waf
    Waf: Entering directory `/home/sanpi/projects/fpga/waf/build'
    [1/7] create_project: src/main.v -> build/blink.prj
    [2/7] create_xst: build/blink.prj -> build/blink.xst
    [3/7] run_xst: build/blink.xst -> build/blink.ngc
    …
    [4/7] ngdbuild: build/blink.ngc -> build/blink.ngd
    …
    [5/7] map: build/blink.ngd -> build/blink.ncd
    …
    [6/7] places_and_routes: build/blink.ncd -> build/blink-routed.ncd
    …
    [7/7] bitgen: build/blink-routed.ncd -> build/blink.bit
    …
    Waf: Leaving directory `/home/sanpi/projects/fpga/waf/build'
    'build' finished successfully (21.857s)

Have fun <3
