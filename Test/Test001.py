import os

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


class DrawIndexedInstancedIndirect:

    pBufferForArgs:str = ""
    AlignedByteOffsetForArgs:int = 0
    hash_value:str = ""

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
        self.pBufferForArgs = args[0].split(":")[1].strip()
        
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
        return (f"pBufferForArgs: {self.pBufferForArgs}, "
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



if __name__ == "__main__":
    # 解限机-机甲-测试
    frameanalysis_folder = r"C:\Users\Administrator\Desktop\net8.0-windows10.0.22621.0\Games\Game001\3Dmigoto\FrameAnalysis-2025-02-25-171130"
    fa = FrameAnalysis(frameanalysis_folder)

    draw_ib = "c3ddbf5a"

    draw_ib_index_list = fa.get_index_list_by_drawib(draw_ib=draw_ib)

    for line in fa.log_lines:
        logline = LogLine(line)

        if logline.call.startswith("DrawIndexedInstancedIndirect"):
            drawcall = DrawIndexedInstancedIndirect(logline.call)

            if logline.index in draw_ib_index_list:
                print(drawcall)
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

    print("ok")