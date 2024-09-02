import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties,FontManager
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog, QTableWidgetItem

def resource_path(relative_path):
    """ 获取资源的绝对路径,用于PyInstaller打包后资源的访问 """
    try:
        # PyInstaller创建的临时文件夹位置
        base_path = sys._MEIPASS
    except Exception:
        # 正常运行时的路径
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def reading(filepath):
    extensions = {
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.xlsb': 'excel',
        '.xlsm': 'excel',
        '.ods': 'odf',
        '.csv': 'csv',
        '.prn': 'csv'
    }
    encodings = ['utf-8', 'gbk', 'ISO-8859-1', 'cp1252', 'utf-16', 'ascii']
    for ext, read_type in extensions.items():
        if filepath.endswith(ext):
            if read_type == 'excel':
                try:
                    df = pd.read_excel(filepath,header=None)
                    print(f"成功读取文件，文件类型为：{ext}")
                    return df
                except Exception as e:
                    print(f"尝试读取{ext}格式文件时发生错误：{e}")
            elif read_type == 'csv' or read_type == 'prn':
                for encoding in encodings:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding,header=None, engine='python')
                        print(f"成功读取文件，使用的编码为：{encoding}")
                        return df
                    except UnicodeDecodeError as e:
                        print(f"尝试编码{encoding}失败：{e}")
                    except Exception as e:
                        print(f"尝试读取文件时发生错误：{e}")        
    print("尝试所有文件类型和编码后仍未能成功读取文件。")
    return None


def setup_table(self, dataframe,table):
        dataframe.columns = dataframe.columns.map(str)
        # 设置表格行列数
        table.setRowCount(dataframe.shape[0])
        table.setColumnCount(dataframe.shape[1])

        # 设置表头
        table.setHorizontalHeaderLabels(dataframe.columns)

        # 填充表格内容
        for i in range(dataframe.shape[0]):
            for j in range(dataframe.shape[1]):
                item_value = str(dataframe.iat[i, j])
                table.setItem(i, j, QTableWidgetItem(item_value))
                
def updata_table(self,ori):
    t:int=-1
    j:int=-1
    k:int=-1
    self.change_bool=True
    hard = {
        '标识':[],
        '标尺读数':[],
        '距离':[],
        '高程':[],
        '站号':[],
        '-1':[],
        '点号标识':[],
        '-2':[],
        '-3':[],
        '前后标志':[],
        '-4':[]
    }
    for index, row in ori.iterrows():
        if row['0']=='B':
            t=index
            print(t)
        if row['0']=='V':
            j=index
            print(f'j={j}')
        if row['0']=='W':
            k=index
            print(f'j={j}')
        if j != -1 and t != -1:
            self.fr=self.ori.iloc[t+1:j]
            self.fr.columns = ['标识','标尺读数','距离','高程','站号','-1','点号标识','-2','-3','前后标志','-4','-5']
            self.fr=self.fr.reset_index()
            self.fr = self.fr.drop('index', axis=1)
            self.fr = self.fr.drop('-5', axis=1)
            self.bk=self.ori.iloc[j+1:k]
            self.bk.columns = ['标识','标尺读数','距离','高程','站号','-1','点号标识','-2','-3','前后标志','-4','-5']
            self.ui.tableWidget.setRowCount(self.fr.shape[0])
            for i in range(self.fr.shape[0]):
                for k in range(self.fr.shape[1]):
                    value = str(self.fr.iat[i,k])
                    self.ui.tableWidget.setItem(i,k,QTableWidgetItem(value))
            self.bk=self.bk.reset_index()
            self.bk = self.bk.drop('index', axis=1)
            self.bk = self.bk.drop('-5', axis=1)
            self.ui.tableWidget_2.setRowCount(self.bk.shape[0])
            for i in range(self.bk.shape[0]):
                for k in range(self.bk.shape[1]):
                    value = str(self.bk.iat[i,k])
                    self.ui.tableWidget_2.setItem(i,k,QTableWidgetItem(value))
    self.change_bool=False
    #self.ui.statusbar.showMessage(self.bk)
    
def change(self,item,data):
    if not self.change_bool:
        row = item.row()
        col = item.column()
        value = item.text()
        data.iloc[row, col] = value
        #self.ui.statusbar.showMessage(data)
#代替以上change函数，确保添加行，删除行的正确性       
def generate_dataframe(self,table):
    if not self.change_bool:
        # 提取 QTableWidget 中的内容到一个新的 DataFrame
        rows = table.rowCount()
        columns = table.columnCount()

        data = []
        for row in range(rows):
            row_data = []
            for column in range(columns):
                item = table.item(row, column)
                if item is not None:
                    row_data.append(item.text())
                else:
                    row_data.append('')
            data.append(row_data)

        # 使用提取的数据生成新的 DataFrame
        new_df = pd.DataFrame(data, columns=[table.horizontalHeaderItem(i).text() for i in range(columns)])
        return new_df
        
def add_row(self,table):
        # 获取当前选中的行
        current_row = table.currentRow()

        if current_row == -1:
            # 如果没有选中任何行，在最后一行后面追加新行
            current_row = table.rowCount()

        # 在指定行后插入新行
        table.insertRow(current_row + 1)
        self.update_indexes(table)

def delete_row(self,table):

        current_row = table.currentRow()
        if current_row >= 0:
            table.removeRow(current_row)
            self.update_indexes(table)
        else:
            return

def update_point(self,table,point_data,dataframe,k):
    i=1+k
    distance=g_num=i_num=g_high=t_g=t_i=i_high=0
    
    for index, row in dataframe.iterrows():

        if row['站号']==i:
            t_g+=1
            distance+=float(row['距离'])
            if row['前后标志']=='B1':
                point_num=row['点号标识']
            else:
                pass
            if row['标识']=='G':
                g_num+=float(row['标尺读数'])
                g_high+=float(row['高程'])
            else:
                pass
            if row['标识']=='I':
                i_num+=float(row['标尺读数'])
            if t_g==4:
                distance/=2
                g_num/=2
                i_num/=2
                detla_h=g_num-i_num
                high=g_high/2
                data={
                    '点号':[point_num],
                    '到下点距离':[distance],
                    '高程':[high],
                    '高程变化量':[detla_h]
                }
                point=pd.DataFrame(data)
                point_data = pd.concat([point_data, point], ignore_index=True)
                i+=1
                distance=g_num=i_num=g_high=t_g=0   
        if t_i==1:
            pass
        if i==float(dataframe.shape[0])/4+k or t_i==4:
            if t_i==0:
                t_i+=1
                continue
            t_i+=1
            if row['前后标志']=='F1':
                last_point_num=row['点号标识']
            if row['标识']=='I':
                i_high+=float(row['高程'])
            if t_i==5:
                high=i_high/2
                data={
                    '点号':[last_point_num],
                    '到下点距离':[0],
                    '高程':[high],
                    '高程变化量':[0]
                }
                point=pd.DataFrame(data)
                point_data = pd.concat([point_data, point], ignore_index=True)
                t_i=i_high=0
                setup_table(self,point_data,table)
                self.symble_type_i=i-1
                return point_data
                
def add_point(self,table,data_point_edge,data,row,fit):
    t=-1
    if fit==False:
        point_data = {
            '点名':[data['点名'][0]],
            '往测点号':[data_point_edge.iloc[row,0]],
            '反测点号':[''],
            '平均高程':[''],
            'x坐标':[data['x坐标'][0]],
            'y坐标':[data['y坐标'][0]],
            '往测高程':[data_point_edge.iloc[row,2]],
            '反测高程':[''],
            '控制高程':[data['高程'][0]],
            '备注':['']
        }
        for index, row in self.point_value.iterrows():
            if point_data['点名'][0]==row['点名']:
                self.point_value.at[index,'往测点号']=point_data['往测点号'][0]
                self.point_value.at[index,'往测高程']=point_data['反测高程'][0]
                if row['x坐标'] != '':
                    self.point_value.at[index,'x坐标']=point_data['x坐标'][0]
                if row['y坐标'] != '':
                    self.point_value.at[index,'y坐标']=point_data['y坐标'][0]
                if row['控制高程'] != '':
                    self.point_value.at[index,'控制高程']=point_data['控制高程'][0]
                if row['反测高程'] != '':
                    self.point_value.at[index,'平均高程']=(float(point_data['往测高程'][0])+float(row['反测高程']))/2
                t=1
        if t==-1:
            self.point_value= pd.concat([self.point_value, pd.DataFrame(point_data)], ignore_index=True)
    elif fit==True:
        point_data = {
            '点名':[data['点名'][0]],
            '往测点号':[''],
            '反测点号':[data_point_edge.iloc[row,0]],
            '平均高程':[''],
            'x坐标':[data['x坐标'][0]],
            'y坐标':[data['y坐标'][0]],
            '往测高程':[''],
            '反测高程':[data_point_edge.iloc[row,2]],
            '控制高程':[data['高程'][0]],
            '备注':['']
        }
        for index, row in self.point_value.iterrows():
            if point_data['点名'][0]==row['点名']:
                self.point_value.at[index,'反测点号']=point_data['反测点号'][0]
                self.point_value.at[index,'反测高程']=point_data['反测高程'][0]
                if row['x坐标'] != '':
                    self.point_value.at[index,'x坐标']=point_data['x坐标'][0]
                if row['y坐标'] != '':
                    self.point_value.at[index,'y坐标']=point_data['y坐标'][0]
                if row['控制高程'] != '':
                    self.point_value.at[index,'控制高程']=point_data['控制高程'][0]
                if row['往测高程'] != '':
                    self.point_value.at[index,'平均高程']=(float(point_data['反测高程'][0])+float(row['往测高程']))/2
                t=1
        if t==-1:
            self.point_value= pd.concat([self.point_value, pd.DataFrame(point_data)], ignore_index=True)
    point_data={}
    t=-1
    self.point_show=self.point_value[['点名','往测点号','反测点号','控制高程','x坐标','y坐标']]
    setup_table(self,self.point_show,self.ui.tableWidget_6)
    self.ui.statusbar.showMessage("读取成功！")
    
def data_to_list(df):
    "将DataFrame的每一行转换为字符串列表"
    string_list = []
    for index, row in df.iterrows():
        formatted_string = f"往测点号: {row['fr点号']}, 反测点号: {row['bk点号']}, 高程差值：{row['Difference']:.5f}, 往测高程: {row['fr高程']}, 反测高程: {row['bk高程']}"
        string_list.append(formatted_string)
    return string_list
    
def predict_class(fr_data,bk_data,fr_key,bk_key):
    column_fr=fr_data[fr_key]
    column_bk=bk_data[bk_key]
    temp_sort=[]
    for i, a in enumerate(column_fr):
        for j, b in enumerate(column_bk):
            difference = abs(a - b)
            temp_sort.append({
                'fr_high': a,
                'fr_index': i,
                'bf_high': b,
                'bk_index': j,
                'Difference': difference
            })
    sorted_results = sorted(temp_sort, key=lambda x: x['Difference'])
    merged_data = []
    for result in sorted_results:
        row_a = fr_data.iloc[result['fr_index']].to_dict()
        row_b = bk_data.iloc[result['bk_index']].to_dict()
        combined_row = {**row_a, **row_b, 'Difference': result['Difference']}
        merged_data.append(combined_row)
    merged_df = pd.DataFrame(merged_data)
    merged_df = merged_df[['fr点号','bk点号','fr高程','bk高程','Difference']]
    return data_to_list(merged_df)

def draw_high_change_plot(self,point_data,row_x,row_y,name,show_bool):
    font_path = resource_path('Yozai-Light.ttf')
    font = FontProperties(fname=font_path)
    FontManager().addfont(font_path)
    
    draw_x=point_data[row_x].values
    draw_y=point_data[row_y].values
    sum_distance=[0]
    t=0
    for d in draw_x:
        sum_distance.append(sum_distance[-1]+d)
    sum_distance = sum_distance[:-1]
    if show_bool==-1:
        plt.figure(figsize=(4,3),dpi=400)
        plt.plot(sum_distance, draw_y, marker='o', linestyle='-', color='b')
        # 添加标题和标签
        plt.title('高程剖面图',fontproperties=font, fontsize=10)
        plt.xlabel('累计距离 (m)',fontproperties=font,fontsize=10)
        plt.ylabel('高程 (m)',fontproperties=font,fontsize=10)
        plt.xticks(sum_distance, fontsize=6)  # 显示每个点的横坐标，设置字体大小为12
        plt.yticks(draw_y, fontsize=6)  # 显示每个点的纵坐标，设置字体大小为12
        plt.grid(False)
        plt.savefig(f'{name}.png')
        plt.close()
    elif show_bool==0:
        plt.figure(figsize=(10,8))
        plt.plot(sum_distance, draw_y, marker='o', linestyle='-', color='b')
        # 添加标题和标签
        plt.title('高程剖面图',fontproperties=font, fontsize=10)
        plt.xlabel('累计距离 (m)',fontproperties=font,fontsize=10)
        plt.ylabel('高程 (m)',fontproperties=font,fontsize=10)
        plt.xticks(sum_distance, fontsize=6)  # 显示每个点的横坐标，设置字体大小为12
        plt.yticks(draw_y, fontsize=6)  # 显示每个点的纵坐标，设置字体大小为12
        plt.grid(False)
        plt.savefig(f'{name}.png')
        plt.show()
    elif show_bool==1:
        if t==0:
            plt.figure(figsize=(10,8))
            plt.plot(sum_distance, draw_y, marker='o', linestyle='-', color='b')
            t=1
        elif t==1:
            plt.plot(sum_distance, draw_y, marker='o', linestyle='-', color='b')
            plt.savefig(f'{name}.png')
            # 添加标题和标签
            plt.title('高程剖面图',fontproperties=font, fontsize=10)
            plt.xlabel('累计距离 (m)',fontproperties=font,fontsize=10)
            plt.ylabel('高程 (m)',fontproperties=font,fontsize=10)
            plt.xticks(sum_distance, fontsize=6)  # 显示每个点的横坐标，设置字体大小为12
            plt.yticks(draw_y, fontsize=6)  # 显示每个点的纵坐标，设置字体大小为12
            plt.grid(False)
            plt.show()
            t=0
            return
        
    elif show_bool==2:
        plt.figure(figsize=(10,8),dpi=300)
        plt.plot(sum_distance, draw_y, marker='o', linestyle='-', color='b')
        # 添加标题和标签
        plt.title('高程剖面图',fontproperties=font, fontsize=10)
        plt.xlabel('累计距离 (m)',fontproperties=font,fontsize=10)
        plt.ylabel('高程 (m)',fontproperties=font,fontsize=10)
        plt.xticks(sum_distance, fontsize=6)  # 显示每个点的横坐标，设置字体大小为12
        plt.yticks(draw_y, fontsize=6)  # 显示每个点的纵坐标，设置字体大小为12
        plt.grid(False)
        plt.savefig(f'{name}.png')
        
def draw_combined_high_change_plot_combine(self, point_data1, point_data2, row_x, row_y, name):
    # 设置字体
    font_path = resource_path('Yozai-Light.ttf')
    font = FontProperties(fname=font_path)
    FontManager().addfont(font_path)
    
    # 处理第一个数据集
    draw_x1 = point_data1[row_x].values
    draw_y1 = point_data1[row_y].values
    sum_distance1 = [0]
    for d in draw_x1:
        sum_distance1.append(sum_distance1[-1] + d)
    sum_distance1 = sum_distance1[:-1]
    
    # 处理第二个数据集
    draw_x2 = point_data2[row_x].values
    draw_y2 = point_data2[row_y].values
    sum_distance2 = [0]
    for d in draw_x2:
        sum_distance2.append(sum_distance2[-1] + d)
    sum_distance2 = sum_distance2[:-1]
    
    # 创建图表
    plt.figure(figsize=(10, 8))
    plt.plot(sum_distance1, draw_y1, marker='o', linestyle='-', color='b', label='往测')
    plt.plot(sum_distance2, draw_y2, marker='o', linestyle='-', color='r', label='反测逆向')
    
    # 添加标题和标签
    plt.title('高程剖面图', fontproperties=font, fontsize=10)
    plt.xlabel('累计距离 (m)', fontproperties=font, fontsize=10)
    plt.ylabel('高程 (m)', fontproperties=font, fontsize=10)
    plt.xticks(fontsize=6)
    plt.yticks(fontsize=6)
    plt.legend(prop=font)
    plt.grid(False)
    
    # 保存和显示图表
    plt.savefig(f'{name}.png')
    plt.show()