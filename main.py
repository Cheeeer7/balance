import sys
import os
import pandas as pd
import numpy as np
import json
from io import BytesIO
from PyQt5.QtCore import Qt,QCoreApplication,QAbstractTableModel,QStringListModel,QRect
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QFileDialog, QTableWidgetItem, QMessageBox, QStyleFactory, QDialog
from PyQt5.QtGui import QFontMetrics,QPixmap,QGuiApplication,QPainter
from ch24 import Ui_MainWindow  
from fountions import reading, setup_table, updata_table, add_row, generate_dataframe, delete_row,update_point,add_point,predict_class,draw_high_change_plot,draw_combined_high_change_plot_combine
from data_require import Ui_Dialog
from adjustment import balance_prepare,balance_,mixed_balance_
from line_balance import *


class DataProcessor:
    def __init__(self):
        global angle_data,lengths
        self.angle_data = angle_data
        self.lengths = lengths

    def process_data(self, df):
        global angle_data,lengths
        # 验证表格数据完整性
        if df.isnull().values.any():
            raise ValueError("DataFrame 中包含缺失值，请检查数据完整性。")

        # 提取角度列，转换为需要的格式
        angles = []
        for angle_str in df['角度']:
            if not angle_str:  # 检查角度字符串是否为空
                print("警告: 角度数据缺失，跳过该条目")
                continue
            degrees, minutes, seconds = self.parse_angle(angle_str)
            angles.append((degrees, minutes, seconds))
        angle_data = angles

        # 提取边长列并保存为列表
        lengths = df['边长'].tolist()

    def parse_angle(self, angle_str):
        # 假设角度是字符串格式的 "21°21′21″"
        # 使用字符串分割提取度、分、秒
        parts = angle_str.replace('°', ' ').replace('′', ' ').replace('″', '').split()
        if len(parts) != 3:
            raise ValueError(f"角度数据格式错误: {angle_str}")
        degrees = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return degrees, minutes, seconds

class PandasModel_line(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df_ = df
        self._df_=self._df_.T


    def rowCount(self, parent=None):
        return self._df_.shape[0]  # 行数等于DataFrame的列数

    def columnCount(self, parent=None):
        return 1  # 只显示一列

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            # 显示列名和对应的值
            
            return f"{self._df_.index[index.row()]}: {str(self._df_.iloc[index.row(), 0])}"
        return None

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df
        

    def rowCount(self, parent=None):
        return len(self._df)  # 行数等于DataFrame的行数

    def columnCount(self, parent=None):
        return 1  # 只显示一列

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            # 获取列名与数值的组合，例如 "列名：数值"
            row_data = " | ".join([f"{self._df.columns[j]}: {str(self._df.iloc[index.row(), j])}" for j in range(self._df.shape[1])])
            return row_data
        return None

class InputDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
        self.pushButton.clicked.connect(self.confirm)
        self.pushButton_2.clicked.connect(self.cancel)
        
    def confirm(self):
        point_name=self.lineEdit.text().strip()
        point_x=self.lineEdit_2.text().strip()
        point_y=self.lineEdit_4.text().strip()
        point_high=self.lineEdit_3.text().strip()
        if point_high=='':
                point_high='待求'
        if point_name=='':
            print('请输入点号！')
            return
        elif point_x == '' or point_y == '':
            print('缺失坐标将无法绘图')
            data={
                '点名':[point_name],
                'x坐标':[point_x],
                'y坐标':[point_y],
                '高程':[point_high]
            }
            self.accept()
            self.point_data=data
        else:
            data={
                '点名':[point_name],
                'x坐标':[point_x],
                'y坐标':[point_y],
                '高程':[point_high]
            }
            self.accept()
            self.point_data=data
    def cancel(self):
        self.reject()
    def get_data(self):
        return getattr(self,'point_data',None)
    

class MainWindow(QMainWindow):
    def __init__(self) :
        global angle_data,lengths
        super().__init__()
        self.ui=Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowTitle("赵旌凯的平差程序")  # 设置窗口标题
        
        self.ui.statusbar.showMessage("准备就绪！")
        
        self.change_bool = False
        self.change_bool_ = False
        self.fr_point=self.bk_point=pd.DataFrame({
                    '点号':[],
                    '到下点距离':[],
                    '高程':[],
                    '高程变化量':[]
                })
        self.point_value=pd.DataFrame({
            '点名':[],
            '往测点号':[],
            '反测点号':[],
            '平均高程':[],
            'x坐标':[],
            'y坐标':[],
            '往测高程':[],
            '反测高程':[],
            '控制高程':[],
            '备注':[]
        })
        self.point_show=pd.DataFrame({
            '点名':[],
            '往测点号':[],
            '反测点号':[],
            '控制高程':[],
            'x坐标':[],
            'y坐标':[]
        })
        self.para_dis_fr=self.para_dis_bk=pd.DataFrame({
            '测段':[],
            '高程变化':[],
            '距离':[],
        })
        self.symble_type_i=0
        self.fr_balance=self.bk_balance=True
        self.is_circle=False
        self.fr_balance_data=self.bk_balance_data=pd.DataFrame(index=[], columns=['点名', '点号', '平差高程'])
        self.mixed_balace=-1
        self.mixed_balance_data=pd.DataFrame({
            '点名':[],
            '往测平差高程':[],
            '反测平差高程':[],
            '往返均衡高程':[]
        })
        self.show_precision=pd.DataFrame({
            'L':[],
            'W':[],
            'K':[],
            'V':[],
            'L^':[]
        })
        self.line_data=pd.DataFrame({
            '点号':[],
            '角度':[],
            '边长':[]
        })
        self.end_result = pd.DataFrame({
                "点号":[],
                "原始坐标x": [],
                "原始坐标y": [],
                "修正后坐标x": [],
                "修正后坐标y": [],
            })
        angle_data=lengths=[]
        self.bal_text=""
        self.fi=-1
        self.start_x=self.start_y=0
        self.current_angle=0
        self.if_line=False
        
        self.ui.pushButton_21.clicked.connect(self.add_line1)
        self.ui.pushButton_22.clicked.connect(self.add_line2)
        self.ui.pushButton_25.clicked.connect(self.add_line3)
        self.ui.pushButton_34.clicked.connect(self.add_line4)
        self.ui.pushButton_23.clicked.connect(self.delete_line1)
        self.ui.pushButton_24.clicked.connect(self.delete_line2)
        self.ui.pushButton_26.clicked.connect(self.delete_line3)
        self.ui.pushButton_27.clicked.connect(self.reset_point)
        self.ui.pushButton.clicked.connect(self.add_point1)
        self.ui.pushButton_3.clicked.connect(self.add_point2)
        self.ui.pushButton_28.clicked.connect(self.show_detail)
        self.ui.pushButton_31.clicked.connect(self.show_detai2)
        self.ui.pushButton_29.clicked.connect(self.show_detai3)
        self.ui.pushButton_32.clicked.connect(self.show_detai4)
        self.ui.pushButton_30.clicked.connect(self.show_detai5)
        self.ui.pushButton_33.clicked.connect(self.show_detai5)
        self.ui.pushButton_6.clicked.connect(self.re_choose)
        self.ui.pushButton_7.clicked.connect(self.balance_fr)
        self.ui.pushButton_8.clicked.connect(self.balance_bk)
        self.ui.pushButton_5.clicked.connect(self.show_list)
        self.ui.pushButton_10.clicked.connect(self.back_list)
        self.ui.pushButton_11.clicked.connect(self.show_list)
        self.ui.pushButton_12.clicked.connect(self.back_list)
        self.ui.pushButton_9.clicked.connect(self.precision)
        
        
        self.ui.action.triggered.connect(self.open_file)
        self.ui.action_2.triggered.connect(self.show_detai6)
        self.ui.action_3.triggered.connect(self.balance)
        self.ui.action_4.triggered.connect(self.save_data)
        self.ui.action_5.triggered.connect(self.load_data)
        self.ui.action_6.triggered.connect(self.high_bal)
        self.ui.action_7.triggered.connect(self.line_bal)
        self.ui.action_8.triggered.connect(self.line_balance)
        self.ui.action_9.triggered.connect(self.save_line)
        self.ui.action_10.triggered.connect(self.read_line_data)
        
        self.ui.tableWidget.itemChanged.connect(self.change1)
        self.ui.tableWidget_2.itemChanged.connect(self.change2)
        self.ui.tableWidget_6.itemChanged.connect(self.change3)
        self.ui.tableWidget_4.cellChanged.connect(self.change4)
        self.ui.tableWidget_5.cellChanged.connect(self.change5)
        self.ui.tableWidget_13.cellChanged.connect(self.change4_)
        
        self.ui.tableWidget_6.cellClicked.connect(self.show1)
        
        self.ui.spinBox.valueChanged.connect(self.value_change)
    
    def line_balance(self):
        processor = DataProcessor()
        try:
            print(self.line_data)
            processor.process_data(self.line_data)
            print(angle_data)
            print(lengths)
            self.current_angle=value_point(self)
            self.start_x=self.ui.lineEdit.text() or "0"
            self.start_y=self.ui.lineEdit_2.text() or "0"
            self.start_x = float(self.start_x)
            self.start_y = float(self.start_y)
            # 计算顶点坐标
            points = calculate_polygon_points(self.start_x, self.start_y, angle_data, lengths,self.current_angle)

            # 计算闭合差
            closure_error_x, closure_error_y = calculate_closure_error(points)

            # 分配闭合差
            corrected_points, corrections = distribute_closure_error(points, lengths, closure_error_x, closure_error_y)
            
            result = {
                "原始坐标x": [],
                "原始坐标y": [],
                "修正后坐标x": [],
                "修正后坐标y": [],
            }

            # 遍历点集，将数据添加到对应的列表中
            for i in range(len(points)):
                original = points[i]
                corrected = corrected_points[i]
                if i == 0:
                    correction = (0, 0)  # 起点不需要修正
                else:
                    correction = corrections[i-1]

                # 添加数据到相应的列表
                result["原始坐标x"].append(original[0])
                result["原始坐标y"].append(original[1])
                result["修正后坐标x"].append(corrected[0])
                result["修正后坐标y"].append(corrected[1])
            result=add_data_(self.line_data,result)
            self.end_result=pd.DataFrame(result)
            columns_to_modify = ['原始坐标x', '原始坐标y', "修正后坐标x", "修正后坐标y"]
            decimal_places = 4
            self.end_result[columns_to_modify] = self.end_result[columns_to_modify].apply(lambda col: col.round(decimal_places))
            
            setup_table(self,self.end_result,self.ui.tableWidget_14)
            
            t1=f"\n坐标闭合差: Δx = {closure_error_x:.4f}, Δy = {closure_error_y:.4f}"
            t2=f"总长度 = {sum(lengths)}"
            t = abs(closure_error_x) * abs(closure_error_y)
            t = math.sqrt(t)
            t = t / sum(lengths)
            t = 1 / t
            t3=f"精度 = 1/{t}"
            temp_line=[t1,t2,t3]
            df = pd.DataFrame(temp_line, columns=['信息'])
            self.show_view(df)
            points = calculate_polygon_points_no(angle_data, lengths)
            self.points=points
            point_labels=self.line_data['点号'].tolist()
            self.point_labels=point_labels
            buf=plot_polygon(points, point_labels, angle_data, lengths,'0')
            image_to_label(buf,self.ui.label)
            buf2=draw_bal(self.end_result,'0')
            image_to_label(buf2,self.ui.label_2)
            
        except ValueError as e:
            self.ui.statusbar.showMessage("错误:", e)
    def line_bal(self):
        self.if_line=True
        self.ui.stackedWidget.setCurrentIndex(3)
    
    def high_bal(self):
        self.if_line=False
        self.ui.stackedWidget.setCurrentIndex(0)
    def save_line(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "保存 JSON 文件", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            try:
                data_to_save = {
                    "line_data": self.line_data.to_dict()
                }
                with open(file_path, 'w') as file:
                    json.dump(data_to_save, file, indent=4)
                QMessageBox.information(self, "提示", "数据保存成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"数据保存失败: {e}")
    def save_data(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "保存 JSON 文件", "", "JSON Files (*.json);;All Files (*)", options=options)
        if file_path:
            try:
                data_to_save = {
                    "ori": self.ori.to_dict(),  # 将 DataFrame 转换为字典
                    "fr_point": self.fr_point.to_dict(),
                    "bk_point": self.bk_point.to_dict(),
                    "point_value": self.point_value.to_dict(),
                    "point_show": self.point_show.to_dict(),
                    "fr": self.fr.to_dict(),
                    "bk": self.bk.to_dict(),
                    "para_dis_fr": self.para_dis_fr.to_dict(),
                    "para_dis_bk": self.para_dis_bk.to_dict(),
                    
                    
                    "predict_list": self.predict_list,
                }
                with open(file_path, 'w') as file:
                    json.dump(data_to_save, file, indent=4)
                QMessageBox.information(self, "提示", "数据保存成功！")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"数据保存失败: {e}")
    def read_line_data(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "打开 JSON 文件", "", "JSON Files (*.json);;All Files (*)", options=options)
        self.change_bool_=True
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    loaded_data = json.load(file)
                    # 恢复数据
                    self.line_data=pd.DataFrame(loaded_data["line_data"])
                    setup_table(self,self.line_data,self.ui.tableWidget_13)
            except Exception as e:
                QMessageBox.warning(self, "错误", f"数据读取失败: {e}")
        self.change_bool_=False
    def load_data(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "打开 JSON 文件", "", "JSON Files (*.json);;All Files (*)", options=options)
        self.change_bool=True
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    loaded_data = json.load(file)
                    # 恢复数据
                    self.ori = pd.DataFrame(loaded_data["ori"])
                    self.fr_point = pd.DataFrame(loaded_data["fr_point"])
                    self.bk_point = pd.DataFrame(loaded_data["bk_point"])
                    self.point_value = pd.DataFrame(loaded_data["point_value"])
                    self.point_show = pd.DataFrame(loaded_data["point_show"])
                    self.fr = pd.DataFrame(loaded_data["fr"])
                    self.bk = pd.DataFrame(loaded_data["bk"])
                    self.para_dis_bk = pd.DataFrame(loaded_data["para_dis_bk"])
                    self.para_dis_fr = pd.DataFrame(loaded_data["para_dis_fr"])
                    
                    self.predict_list = loaded_data["predict_list"]
                setup_table(self,self.ori,self.ui.tableWidget_3)
                setup_table(self,self.fr_point,self.ui.tableWidget_4)
                setup_table(self,self.bk_point,self.ui.tableWidget_5)
                setup_table(self,self.fr,self.ui.tableWidget)
                setup_table(self,self.bk,self.ui.tableWidget_2)
                setup_table(self,self.point_show,self.ui.tableWidget_6)
                self.show_view( self.point_value)
                
                model = QStringListModel()
                model.setStringList(self.predict_list)
                self.ui.listView.setModel(model)
                draw_high_change_plot(self,self.fr_point,'到下点距离','高程',"fr_point",-1)
                pixmap = QPixmap('fr_point.png')
                scaled_pixmap = pixmap.scaled(self.ui.label.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation)
                self.ui.label.setPixmap(scaled_pixmap)
                
                draw_high_change_plot(self,self.bk_point,'到下点距离','高程',"bk_point",-1)
                pixmap = QPixmap('bk_point.png')
                scaled_pixmap = pixmap.scaled(self.ui.label_2.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation)
                self.ui.label_2.setPixmap(scaled_pixmap)
            
                
                QMessageBox.information(self, "提示", "数据读取成功！")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"数据读取失败: {e}")
        self.change_bool=False
        
    def precision(self):
        global A_matrix,Q_matrix,N_aa_matrix
        self.ui.stackedWidget.setCurrentIndex(2)
        
        setup_table(self,self.show_precision,self.ui.tableWidget_12)
        self.ui.label.setText("单位权中误差为：\n"+str(self.fi))
        self.ui.label_2.setText(self.bal_text)
        
        
    def show_list(self):
        self.ui.stackedWidget.setCurrentIndex(1)
    def back_list(self):
        self.ui.stackedWidget.setCurrentIndex(0)
    
    def balance_fr(self):
        if self.fr_balance==False:
            QMessageBox.warning(self, "错误", f"往测信息不全")
            return
        balance_(self,self.para_dis_fr,self.point_value,'fr')
        self.mixed_balace*=-1
        if self.mixed_balace==-2:
            mixed_balance_(self,self.para_dis_fr,self.para_dis_bk)
        
    def balance_bk(self):
        if self.bk_balance==False:
            QMessageBox.warning(self, "错误", f"往测信息不全")
            return
        balance_(self,self.para_dis_bk,self.point_value,'bk')
        self.mixed_balace*=-2
        if self.mixed_balace==-2:
            mixed_balance_(self,self.fr_balance_data,self.bk_balance_data)
    
    def re_choose(self):
        self.ui.stackedWidget_2.setCurrentIndex(0)
        self.mixed_balace=-1
        self.fr_balance=self.bk_balance=True
        self.is_circle=False
        self.fr_balance_data=self.bk_balance_data=pd.DataFrame(index=[], columns=['点名', '点号', '平差高程'])
        self.mixed_balace=-1
        self.mixed_balance_data=pd.DataFrame({
            '点名':[],
            '往测平差高程':[],
            '反测平差高程':[],
            '往返均衡高程':[]
        })
    
    def balance(self):
        self.ui.stackedWidget_2.setCurrentIndex(3)
        self.fr_balance=self.bk_balance=True
        for index, row in self.point_value.iterrows():
            if row['备注']=='信息严重不全':
                self.point_value=self.point_value.drop(index)
                QMessageBox.warning(self, "错误", f"{row['点名']}信息严重不全,已经删除")
                continue
            if row['备注']=='往测信息不全':
                self.fr_balance=False
                QMessageBox.warning(self, "错误", f"{row['点名']}往测信息不全")
            if row['备注']=='反测信息不全':
                self.bk_balance=False
                QMessageBox.warning(self, "错误", f"{row['点名']}反测信息不全")
        self.point_value=self.point_value.reset_index(drop=True)
        if self.fr_balance==True:
            balance_prepare(self,self.point_value,self.fr_point,self.para_dis_fr,'fr')
        if self.bk_balance==True:
            temp_bk_point=self.bk_point.iloc[::-1].reset_index(drop=True)
            balance_prepare(self,self.point_value,temp_bk_point,self.para_dis_bk,'bk')
        
        
    def show_detail(self):
        if self.if_line==False:
            draw_high_change_plot(self,self.fr_point,'到下点距离','高程',"fr_point",0)
        else:
            plot_polygon(self.points, self.point_labels, angle_data, lengths, -1)
    def show_detai2(self):
        if self.if_line==False:
            draw_high_change_plot(self,self.bk_point,'到下点距离','高程',"bk_point",0)
        else:
            draw_bal(self.end_result,-1)
        
    def show_detai3(self):
        if self.if_line==True:
            return
        self.ui.stackedWidget_2.setCurrentIndex(1)
        draw_high_change_plot(self,self.fr_point,'到下点距离','高程',"fr_point_detail",2)
        pixmap = QPixmap('fr_point_detail.png')
        scaled_pixmap = pixmap.scaled(self.ui.label_6.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.ui.label_6.setPixmap(scaled_pixmap)
        self.ui.label_6.setScaledContents(True)
        
    def show_detai4(self):
        if self.if_line==True:
            return
        self.ui.stackedWidget_2.setCurrentIndex(2)
        draw_high_change_plot(self,self.bk_point,'到下点距离','高程',"bk_point_detail",2)
        pixmap = QPixmap('bk_point_detail.png')
        scaled_pixmap = pixmap.scaled(self.ui.label_6.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.ui.label_7.setPixmap(scaled_pixmap)
        self.ui.label_7.setScaledContents(True)
    def show_detai5(self):
        self.ui.stackedWidget_2.setCurrentIndex(0)
    def show_detai6(self):
        temp_bk_point=self.bk_point
        temp_bk_point['到下点距离'] = temp_bk_point['到下点距离'].shift(1, fill_value=0)
        temp_bk_point = temp_bk_point.iloc[::-1].reset_index(drop=True)
        draw_combined_high_change_plot_combine(self, self.fr_point, temp_bk_point, '到下点距离', '高程', "combined_point_detail")
        
    def value_change(self,value):
        if value>0:
            t=value
            temp_line=self.predict_list[:t]
            model = QStringListModel()
            model.setStringList(temp_line)
            self.ui.listView.setModel(model)
        else:
            t=0
        
        
    def show_Clicked_row(self,new_df,index):
        # 提取该行数据，并将其转换为垂直显示的DataFrame
        selected_row = new_df.iloc[index].to_frame().T
        selected_row_model = PandasModel_line(selected_row)

        # 设置模型并调小行高
        self.ui.tableView.setModel(selected_row_model)
        self.adjust_row_heights_line()

    def adjust_row_heights_line(self):
        for row in range(self.ui.tableView.model().rowCount()):
            self.ui.tableView.setRowHeight(row, 20)  # 将每行的高度设置为20像素
        
    def adjust_row_heights(self):
        "自动调整行距"
        font_metrics = QFontMetrics(self.ui.tableView.font())
        for row in range(self.ui.tableView.model().rowCount()):
            text = self.ui.tableView.model().data(self.ui.tableView.model().index(row, 0))
            text_height = font_metrics.boundingRect(0, 0, self.ui.tableView.columnWidth(0), 0, Qt.TextWordWrap, text).height()
            self.ui.tableView.setRowHeight(row, text_height + 10)  # 额外增加一点高度
    def show_view(self,df):
        model = PandasModel(df)
        self.ui.tableView.setModel(model)
        #self.ui.tableView.horizontalHeader().setVisible(False)
        self.ui.tableView.verticalHeader().setVisible(False)
        # 启用自动换行
        self.ui.tableView.setWordWrap(True)
        # 调整行高以适应内容
        self.adjust_row_heights()
        
    def show1(self,row,column):
        if row in self.point_value.index:
            
            self.show_Clicked_row(self.point_value,row)
            self.ui.tableView.horizontalHeader().setVisible(True)
        
    def reset_point(self):
        for index_show, row_show in self.point_show.iterrows():
            if row_show['点名']:
                if row_show['控制高程']=='':
                    self.point_show.loc[index_show, '控制高程'] = '待求'
        self.point_value=pd.DataFrame({
            '点名':[],
            '往测点号':[],
            '反测点号':[],
            '平均高程':[],
            'x坐标':[],
            'y坐标':[],
            '往测高程':[],
            '反测高程':[],
            '控制高程':[],
            '备注':[]
        })
        for index_show, row_show in self.point_show.iterrows():
            t_1=t_2=-1
            t_x=t_y=0
            for index_fr, row_fr in self.fr_point.iterrows():
                if row_show['往测点号']==row_fr['点号']:
                    fr_high=row_fr['高程']
                    t_1=1
            for index_bk, row_bk in self.bk_point.iterrows():
                if row_show['反测点号']==row_bk['点号']:
                    bk_high=row_bk['高程']
                    t_2=2
            if 'x坐标' in row_show:
                if row_show['x坐标']:  # 进一步检查是否有值
                    coor_x = row_show['x坐标']
                    t_x=1
                else :
                    coor_x = ''
            if 'y坐标' in row_show:
                if row_show['y坐标']:  # 进一步检查是否有值
                    coor_y = row_show['y坐标']
                    t_y=1
                else :
                    coor_y = ''
            if row_show['反测点号']=='' or row_show['往测点号']=='':
                tip='信息不全'
            if t_x*t_y==0:
                tip='绘图信息不全'
            else:
                tip=''
            if t_1*t_2==1:#仅有点名
                point_data = {
                '点名':[row_show['点名']],
                '往测点号':[''],
                '反测点号':[''],
                '平均高程':[''],
                'x坐标':[coor_x],
                'y坐标':[coor_y],
                '往测高程':[''],
                '反测高程':[''],
                '控制高程':[row_show['控制高程']],
                '备注':['信息严重不全']
                }
                self.ui.statusbar.showMessage(f"第{row_show['点名']}点信息不全，请检查输入点号")
            elif t_1*t_2==-1:#有往无反
                point_data = {
                '点名':[row_show['点名']],
                '往测点号':[row_show['往测点号']],
                '反测点号':[''],
                '平均高程':[''],
                'x坐标':[coor_x],
                'y坐标':[coor_y],
                '往测高程':[fr_high],
                '反测高程':[''],
                '控制高程':[row_show['控制高程']],
                '备注':['反测信息不全']
                }
                self.ui.statusbar.showMessage(f"第{row_show['点名']}点信息不全，缺少反测数据！")
            elif t_1*t_2==-2:#有反无往
                point_data = {
                '点名':[row_show['点名']],
                '往测点号':[''],
                '反测点号':[row_show['反测点号']],
                '平均高程':[''],
                'x坐标':[coor_x],
                'y坐标':[coor_y],
                '往测高程':[''],
                '反测高程':[bk_high],
                '控制高程':[row_show['控制高程']],
                '备注':['往测信息不全']
                }
                self.ui.statusbar.showMessage(f"第{row_show['点名']}点信息不全，缺少往测数据！")
            elif t_1*t_2==2:#齐活
                avg_high=(float(fr_high)+float(bk_high))/2
                point_data = {
                '点名':[row_show['点名']],
                '往测点号':[row_show['往测点号']],
                '反测点号':[row_show['反测点号']],
                '平均高程':[avg_high],
                'x坐标':[coor_x],
                'y坐标':[coor_y],
                '往测高程':[fr_high],
                '反测高程':[bk_high],
                '控制高程':[row_show['控制高程']],
                '备注':[tip]
                }
            self.point_value= pd.concat([self.point_value, pd.DataFrame(point_data)], ignore_index=True)
        self.show_view( self.point_value)
    
    def add_point1(self):
        current_row = self.ui.tableWidget_4.currentRow()
        if current_row == -1:
            print('请选中一行')
        else:
            dialog = InputDialog()
            if dialog.exec_() == QDialog.Accepted:
                data=dialog.get_data()
                add_point(self,self.ui.tableWidget_4,self.fr_point,data,current_row,False)
    def add_point2(self):
        current_row = self.ui.tableWidget_5.currentRow()
        if current_row == -1:
            self.ui.statusbar.showMessage('请选中一行')
        else:
            dialog = InputDialog()
            if dialog.exec_() == QDialog.Accepted:
                data=dialog.get_data()
                add_point(self,self.ui.tableWidget_5,self.bk_point,data,current_row,True)
        
    def update_indexes(self,table):
        # 更新每一行的垂直头，使其显示正确的行号
        for row in range(self.ui.tableWidget.rowCount()):
            table.setVerticalHeaderItem(row, QTableWidgetItem(str(row + 1)))
        
    def add_line1(self):
        add_row(self,self.ui.tableWidget)
    def add_line2(self):
        add_row(self,self.ui.tableWidget_2)
    def add_line3(self):
        add_row(self,self.ui.tableWidget_6)
    def add_line4(self):
        add_row(self,self.ui.tableWidget_13)
        last_row_index=self.ui.tableWidget_13.rowCount()-1
        item = QTableWidgetItem("°′″")
        self.ui.tableWidget_13.setItem(last_row_index,1,item)
    def delete_line1(self):
        delete_row(self,self.ui.tableWidget)
        self.change1()
    def delete_line2(self):
        delete_row(self,self.ui.tableWidget_2)
        self.change2()
    def delete_line3(self):
        delete_row(self,self.ui.tableWidget_6)
        self.change3()
    def delete_line4(self):
        delete_row(self,self.ui.tableWidget_13)
        self.change4_()
    

    def open_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "选择文件", "", "All Files (*);;Text Files (*.txt)", options=options)
        if file_name:
            self.ori=reading(file_name)
            setup_table(self,self.ori,self.ui.tableWidget_3)
            updata_table(self,self.ori)
            self.change_bool=True
            fr_point=bk_point=pd.DataFrame({
                    '点号':[],
                    '到下点距离':[],
                    '高程':[],
                    '高程变化量':[]
                })
            self.fr_point=update_point(self,self.ui.tableWidget_4,fr_point,self.fr,self.symble_type_i)
            self.bk_point=update_point(self,self.ui.tableWidget_5,bk_point,self.bk,self.symble_type_i)
            self.symble_type_i=0
            
            fr_temp=self.fr_point.rename(columns={'高程': 'fr高程', '点号': 'fr点号'}, inplace=False)
            bk_temp=self.bk_point.rename(columns={'高程': 'bk高程', '点号': 'bk点号'}, inplace=False)
            fr_temp = fr_temp.iloc[::2].reset_index(drop=True)
            bk_temp = bk_temp.iloc[::2].reset_index(drop=True)
            self.predict_list=predict_class(fr_temp,bk_temp,'fr高程','bk高程')
            model = QStringListModel()
            model.setStringList(self.predict_list)
            self.ui.listView.setModel(model)
            
            draw_high_change_plot(self,self.fr_point,'到下点距离','高程',"fr_point",-1)
            pixmap = QPixmap('fr_point.png')
            scaled_pixmap = pixmap.scaled(self.ui.label.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation)
            self.ui.label.setPixmap(scaled_pixmap)
            
            draw_high_change_plot(self,self.bk_point,'到下点距离','高程',"bk_point",-1)
            pixmap = QPixmap('bk_point.png')
            scaled_pixmap = pixmap.scaled(self.ui.label_2.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation)
            self.ui.label_2.setPixmap(scaled_pixmap)
            
            self.change_bool=False
            
    
    def change1(self):
        #change(self,item,self.fr)
        if not self.change_bool:
            ttt=generate_dataframe(self,self.ui.tableWidget)
            self.fr=ttt
    def change2(self):
        if not self.change_bool:
            ttt=generate_dataframe(self,self.ui.tableWidget_2)
            self.bk=ttt
    def change3(self):
        if not self.change_bool:
            ttt=generate_dataframe(self,self.ui.tableWidget_6)
            self.point_show=ttt
    def change4_(self):
        if not self.change_bool_:
            ttt=generate_dataframe(self,self.ui.tableWidget_13)
            self.line_data=ttt
    def change4(self,row,column):
        if not self.change_bool:
            if column == 2:
                reply = QMessageBox.question(self, '确认修改', 
                                     f"你确定要修改第 {self.fr_point.iloc[row,0]} 号点高程，作为基准高程吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    item = self.ui.tableWidget_4.item(row, column)
                    if item is not None:
                        # 将文本内容转换为浮点数
                        new_high = float(item.text())
                    else:
                        self.ui.statusbar.showMessage('请入正确的数值')
                    old_high=float(self.fr_point.iloc[row,column])
                    detla_high=new_high-old_high
                    self.change_bool=True
                    self.fr_point['高程']+=detla_high
                    self.bk_point['高程']+=detla_high
                    setup_table(self,self.fr_point,self.ui.tableWidget_4)
                    setup_table(self,self.bk_point,self.ui.tableWidget_5)
                    fr_temp=self.fr_point.rename(columns={'高程': 'fr高程', '点号': 'fr点号'}, inplace=False)
                    bk_temp=self.bk_point.rename(columns={'高程': 'bk高程', '点号': 'bk点号'}, inplace=False)
                    fr_temp = fr_temp.iloc[::2].reset_index(drop=True)
                    bk_temp = bk_temp.iloc[::2].reset_index(drop=True)
                    self.predict_list=predict_class(fr_temp,bk_temp,'fr高程','bk高程')
                    model = QStringListModel()
                    model.setStringList(self.predict_list)
                    self.ui.listView.setModel(model)
                    self.change_bool=False
                else:
                    self.change_bool=True
                    setup_table(self,self.fr_point,self.ui.tableWidget_4)
                    self.change_bool=False
    def change5(self,row,column):
        if not self.change_bool:
            if column == 2:
                reply = QMessageBox.question(self, '确认修改', 
                                     f"你确定要修改第 {self.bk_point.iloc[row,0]} 号点高程，作为基准高程吗？",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    item = self.ui.tableWidget_5.item(row, column)
                    if item is not None:
                        # 将文本内容转换为浮点数
                        new_high = float(item.text())
                    else:
                        self.ui.statusbar.showMessage('请入正确的数值')
                    old_high=float(self.bk_point.iloc[row,column])
                    detla_high=new_high-old_high
                    self.change_bool=True
                    self.fr_point['高程']+=detla_high
                    self.bk_point['高程']+=detla_high
                    setup_table(self,self.fr_point,self.ui.tableWidget_4)
                    setup_table(self,self.bk_point,self.ui.tableWidget_5)
                    self.change_bool=False
                else:
                    self.change_bool=True
                    setup_table(self,self.bk_point,self.ui.tableWidget_5)
                    self.change_bool=False
           

            
if __name__ == "__main__":
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)  # 使能高DPI缩放
    #os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'E:\codeC\py_平差\ch24pc\Lib\site-packages\PyQt5\Qt5\plugins\platforms'
    app=QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("WindowsVista"))
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())