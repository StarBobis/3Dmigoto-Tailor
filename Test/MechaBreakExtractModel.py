import os
import numpy as np


class LogLine:
    index:str = ""
    call:str = ""

    def __init__(self,log_line:str) -> None:
        # 提取前六位作为 Index
        self.index = log_line[:6]
        
        # 找到第一个空格的位置
        first_space_index = log_line.find(' ')

        # 提取第一个空格之后的内容作为 call
        self.call = log_line[first_space_index + 1:]

class PBufferForArgs:
    # 所有参数都是UINT类型的，这里用INT代替因为数值不会特别大
    IndexCountPerInstance:int = 0
    InstanceCount:int = 0
    StartIndexLocation:int = 0
    BaseVertexLocation:int = 0
    StartInstanceLocation:int = 0

    def __init__(self,buf_file_path:str,AlignedByteOffsetForArgs:int) -> None:
        numberlist = np.fromfile(index_filepath, dtype=np.uint32).tolist()
        offset:int = int(AlignedByteOffsetForArgs / 20 * 5) 
        # print(offset)
        # print(numberlist)
        # print(numberlist[offset*5:offset*5 + 5])
        self.IndexCountPerInstance = numberlist[offset]
        self.InstanceCount = numberlist[offset + 1]
        self.StartIndexLocation = numberlist[offset + 2]
        self.BaseVertexLocation = numberlist[offset + 3]
        self.StartInstanceLocation = numberlist[offset + 4]
        
    def __str__(self) -> str:
        # 返回类的属性信息字符串
        return (
            f"IndexCountPerInstance: {self.IndexCountPerInstance}\n"
            f"InstanceCount: {self.InstanceCount}\n"
            f"StartIndexLocation: {self.StartIndexLocation}\n"
            f"BaseVertexLocation: {self.BaseVertexLocation}\n"
            f"StartInstanceLocation: {self.StartInstanceLocation}"
        )

class DrawIndexedInstancedIndirect:

    pBufferForArgs_str:str = ""
    AlignedByteOffsetForArgs:int = 0
    hash_value:str = ""
    pBufferForArgs:PBufferForArgs = None

    def __init__(self, call_str: str) -> None:
        # 找到括号内的内容
        start = call_str.find("(")
        end = call_str.find(")")
        if start == -1 or end == -1:
            raise ValueError("输入字符串格式不正确，无法解析")
        
        # 提取括号内的内容
        args_str = call_str[start + 1:end]
        
        # 按逗号分割参数
        args = args_str.split(", ")
        
        # 提取 pBufferForArgs
        if len(args) < 2 or not args[0].startswith("pBufferForArgs:"):
            raise ValueError("输入字符串格式不正确，无法解析 pBufferForArgs")
        self.pBufferForArgs_str = args[0].split(":")[1].strip()
        
        # 提取 AlignedByteOffsetForArgs
        if not args[1].startswith("AlignedByteOffsetForArgs:"):
            raise ValueError("输入字符串格式不正确，无法解析 AlignedByteOffsetForArgs")
        self.AlignedByteOffsetForArgs = int(args[1].split(":")[1].strip())
        
        # 提取 hash_value
        hash_start = call_str.find("hash=")
        if hash_start == -1:
            raise ValueError("输入字符串格式不正确，无法解析 hash_value")
        self.hash_value = call_str[hash_start + 5:].strip()

    def __str__(self):
        return (f"pBufferForArgs: {self.pBufferForArgs_str}, "
                f"AlignedByteOffsetForArgs: {self.AlignedByteOffsetForArgs}, "
                f"hash_value: {self.hash_value}")


class FrameAnalysis:
    frameanalysis_folder_path:str = ""
    frameanalysis_log_path:str = ""

    log_lines:list[str] = []

    def __init__(self,frameanalysis_folder_path:str) -> None:
        self.frameanalysis_folder_path = frameanalysis_folder_path
        self.frameanalysis_log_path = self.frameanalysis_folder_path + "\\" + "log.txt"

        with open(self.frameanalysis_log_path, 'r', encoding='utf-8') as file:
            self.log_lines = file.readlines()

    def get_index_list_by_drawib(self,draw_ib:str) -> list[str]:
        draw_ib_index_list = []
        for line in self.log_lines:
            logline = LogLine(line)
            if "hash=" + draw_ib in logline.call:
                draw_ib_index_list.append(logline.index)
                # print(logline.index)
        return draw_ib_index_list
    
    def filter_frameanalysis_files(self,contains_str:str,suffix_str:str) -> list[str]:
        filtered_filename_list = []
        for frameanalysis_file in os.listdir(self.frameanalysis_folder_path):
            # print(frameanalysis_file)
            if contains_str in frameanalysis_file and frameanalysis_file.endswith(suffix_str):
                filtered_filename_list.append(frameanalysis_file)

        return filtered_filename_list
    
    def filter_first_frameanalysis_file(self,contains_str:str,suffix_str:str) -> str:
        filter_list = self.filter_frameanalysis_files(contains_str=contains_str,suffix_str=suffix_str)
        return filter_list[0]
    
    def filter_files(self,filter_folder:str,contains_str:str,suffix_str:str) -> list[str]:
        filtered_filename_list = []
        for filename in os.listdir(filter_folder):
            # print(frameanalysis_file)
            if contains_str in filename and filename.endswith(suffix_str):
                filtered_filename_list.append(filename)

        return filtered_filename_list


if __name__ == "__main__":
    # 解限机-机甲-测试
    frameanalysis_folder = r"C:\Users\Administrator\Desktop\net8.0-windows10.0.22621.0\Games\Game001\3Dmigoto\FrameAnalysis-2025-02-28-115121"
    fa = FrameAnalysis(frameanalysis_folder)

    draw_ib = "c3ddbf5a"

    draw_ib_index_list = fa.get_index_list_by_drawib(draw_ib=draw_ib)

    index_drawcall_dict:dict[str,DrawIndexedInstancedIndirect] = {}
    for line in fa.log_lines:
        logline = LogLine(line)

        if logline.call.startswith("DrawIndexedInstancedIndirect"):
            drawcall = DrawIndexedInstancedIndirect(logline.call)

            if logline.index in draw_ib_index_list:
                # print(drawcall)
                '''
                观察可以发现，不止一个Hash值，调用DrawIndexedInstancedIndirect传入的参数
                
                两种方案：
                1.根据这里的Index获取每一个VS的Hash值，随后用
                [ShaderOverride_XXX]
                hash = XXX
                dump = this
                的方式来dump DrawIndexedInstancedIndirect的参数Buffer，
                随后从其中根据当前调用的AlignedByteOffsetForArgs来找到对应的调用参数
                此时这些参数应该就是传递到Shader中的v4.xyz v3.xyz等等

                2.修改3Dmigoto源码，在调用FrameAnalysisContext::DrawInstancedIndirect时
                把这个DrawIndexedInstancedIndirect的参数的Hash值中的内容Dump出来。

                
                
                '''
                index_drawcall_dict[logline.index] = drawcall

    # 之前我们在d3d11.dll中实现了dump DrawIndexedInstancedIndirect的参数，现在可以直接解析Buffer文件来读取参数
    # 后续这些参数的值，配合Shader中的逻辑，以及偏移量对应的参数，就能正确的知道传递到Shader里的v开头的变量的内容是什么了。

    # 现在根据这些Index来找对应的Buffer，然后看一下里面的内容都有什么，看一下里面的内容是否都一样。
    # -drawindexedinstancedindirect=
    # index_count = 0
    
    index_fulldrawcall_dict:dict[str:DrawIndexedInstancedIndirect] = {}
    for key, value in index_drawcall_dict.items():
        print("index:" + key + " drawcall" + str(value))
        index_filename_list = fa.filter_frameanalysis_files(key,".buf")

        for index_filename in index_filename_list:
            # 这个Buffer是dump下来的，基础的3Dmigoto没有这个功能，我加上去的
            # 可以在这个issue中看到具体添加方法：
            # https://github.com/bo3b/3Dmigoto/issues/356#issuecomment-2683749651
            if "-drawindexedinstancedindirect=" in index_filename:
                print(index_filename)
                index_filepath = fa.frameanalysis_folder_path + "\\" + index_filename

                pBufferForArgs = PBufferForArgs(index_filepath,value.AlignedByteOffsetForArgs)
                print(str(pBufferForArgs))
                value.pBufferForArgs = pBufferForArgs

                index_fulldrawcall_dict[key] = value
            
        # index_count += 1
        # if index_count > 5:
        #     break
        print("-------------------------------------------------------------------")

    # 测试完了，确实可以拿到具体的pBufferForArgs参数，接下来的内容就是逆向Shader，根据Shader中对这几个参数的处理，模拟Shader的处理方式
    # 从vs-t0到vs-t6中读取数据，提取出对应偏移段的模型。
    # 正常情况下，我们用到的参数应该只有InndexCountPerInstance和InstanceCount，其它的参数应该都为0。

    for index, drawcall in index_drawcall_dict.items():
        first_ib_file = fa.filter_first_frameanalysis_file(index + "-ib=",".buf")
        print(first_ib_file)
        '''
        000051-ib=c3ddbf5a-vs=bbbc0e987083d940-ps=c40ab7467e0b3b5c.buf
        000052-ib=c3ddbf5a-vs=bbbc0e987083d940-ps=241011bfadb9d50d.buf
        000053-ib=c3ddbf5a-vs=82d10c405be5974f-ps=7d72979950459e0e.buf
        000054-ib=c3ddbf5a-vs=bbbc0e987083d940-ps=c40ab7467e0b3b5c.buf
        000055-ib=c3ddbf5a-vs=fb413544c99a69f3-ps=41abdb8cc400c7b7.buf
        000056-ib=c3ddbf5a-vs=bbbc0e987083d940-ps=c40ab7467e0b3b5c.buf

        那么问题来了，这些不同的Index使用了不同的VS值，是否意味着每一个VS中的内容都不同呢
        如果不同，是不是每一个类型的Shader都需要写单独的解析逻辑？
        所以接下来需要开游戏测试，先dump几个vs看看内容是否相同。

        初步推测可能是一部分VS负责位置Position和Blend信息，一部分Shader负责TANGENT、Normal信息
        一部分Shader负责UV贴图，当然这个只是猜测，具体还得进游戏Dump Shader来查看。
        '''
        

    '''
    进入游戏测试发现，果然每个VS都只负责一部分信息，有的负责场景，有的负责机甲，它们都在一个IndexBuffer里。。。
    所以对于不同类型的模型，要编写不同类型的脚本才行。

    既然机甲的模型和场景的模型使用的Shader是不同的，那么现在先关注机甲的模型提取。

    经过测试vs为4c9cec64b0195573的Shader dump下来光ASM就有3000行，加上解析失败的HLSL一共有6000行左右
    为什么会这么大？
    是提交的Buffer数据中含有加密数据，然后VertexShader中做了混淆解密处理吗？？？
    如果真的做了混淆加密才传递到Buffer中，然后利用控制流混淆的代码进行解密，那即使能够使用偏移拿到正确的数据
    后续解密的流程要如何还原，要如何把解混淆的ASM代码转换为python或者C++等代码，再实现一次呢。

    但是这个VS就是控制机甲渲染的核心代码，其它的VS只是机甲身上的一些装饰,光效等等，要提取模型就绕不过这个Shader的处理。
    '''
    
    '''
    
    经过确定，使用了代码混淆技术，传递到Buffer中的内容是加密后的，在Shader中进行解密
    但是Shader的代码被膨胀和混淆了，要解决这个问题，只能开发模拟执行的解混淆工具或者别的什么的。。。
    '''

    '''
    虽然混淆了Shader，但是还是有机会解开的
    1.把Shader dump为二进制格式，用更高级的工具进行分析逆向，去掉混淆代码和无效代码。
    2.直接模拟Shader的执行流程，把得到的中间结果，也就是原始姿态的模型从中间执行结果中拿出来。
    
    
    '''





    print("ok")