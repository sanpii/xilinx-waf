# Xilinx feature for Waf

Use [waf](https://code.google.com/p/waf/) for compile xilinx verilog sources.

## Installation

Copy ``xilinx.py`` in your source directory or use git submodule:

    $ git submodule add git://github.com/sanpii/xilinx-waf.git

## Usage

Create ``wscript``:

    #!/usr/bin/env python

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

    def simulate(bld):
        bld(
            target = "blink",
            source = ["src/main.v", "src/blinkTest.v"]
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
    Checking for program fuse                : /opt/Xilinx/14.5/ISE_DS/ISE/bin/lin64/fuse
    Checking for program vlogcomp            : /opt/Xilinx/14.5/ISE_DS/ISE/bin/lin64/vlogcomp
    'configure' finished successfully (0.009s)

Simulate:

    $ ./waf sim
    …
    'sim' finished successfully (1.868s)
    $ source /opt/Xilinx/14.5/ISE_DS/settings64.sh
    $ cd build
    $ ./blink_bench.exe -gui

Synthetize:

    $ ./waf
    …
    'build' finished successfully (21.857s)

Have fun <3
