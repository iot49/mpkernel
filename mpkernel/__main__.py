from ipykernel.kernelapp import IPKernelApp

from . import MpKernel

IPKernelApp.launch_instance(kernel_class=MpKernel)
