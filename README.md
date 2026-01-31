# Thermalright_LCD
Display script for the Mjolnir Vision X 360 WHITE screen.
LCD display script independent of the official TRCC software, based on [chizhu Tech] solution.


1.Device Port：
    VID = 0x87AD
    PID = 0x70DB

    
2.Displayed as 'USBDISPLAY' in Device Manager.


3.Featuring an independent MCU, displays the Thermalright logo when there is no input.
###############################################################################################


Send an image frame using a header parameter: "123456780000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000123456780200000040010000f00000000000000000000000000000000000000000000000000000000000000000000000000000000000002000000" + "JPEG little-endian" + "0000"; +'Jpeg_hex'.



###############################################################################################

讲人话：一个帧头是一串16进制+图片大小的编码+0000。后边跟上jpg图的hex编码，发送出去就显示图了。

样本我传上来，不一样就只能你自己去抓包了。


###############################################################################################


避坑：头文件不要复制粘贴，保存不要用文本文档，尽量用脚本去转。不然这辈子可能是弄不亮了。屏幕接收到包就会显示一下，持续发包持续显示，没有初始化那些东西。
