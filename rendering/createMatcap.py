# -*- coding: utf-8 -*-
from maya import cmds
from PySide2 import QtWidgets, QtCore, QtGui
import os
import sys
import math
from ..lib import qt
# ファイルのパスを取得
CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
# matcapの画像が入ったフォルダの名前
FOLDER = "matcaps"
# テーブルのカラム数
COLUMN = 4
# マットキャップマテリアルの名前
MATERIAL_NAME = "Matcap_mat"


class CustomTableModel(QtCore.QAbstractTableModel):
    """
    カスタムのモデルを作る
    """

    def __init__(self, parent=None, data=[]):
        super(CustomTableModel, self).__init__(parent)
        # マトリクスのデータを受け取りitemに格納する
        self.__item = data

    # アイテムの数を返す
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__item)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return COLUMN

    # Roleに合わせてデータを返す
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        if not 0 <= index.row() < len(self.__item):
            return None
        if role == QtCore.Qt.DisplayRole:
            return "name"
        elif role == QtCore.Qt.ForegroundRole:
            return QtGui.QColor(30, 30, 30)
        # thumbnailキーの画像ファイル名を返す
        elif role == QtCore.Qt.UserRole:
            return self.__item[index.row()][index.column()]

        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        else:
            return None

    # データ変更時の処理
    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or not 0 <= index.row() < len(self.__item):
            return False
        if role == QtCore.Qt.EditRole and value != "":
            # self.__item[index.row()]["name"] = value
            # self.dataChanged.emit(index,index)
            return True
        else:
            return False

    # 各セルのインタラクション
    def flags(self, index):
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled


class CustomTableDelegate(QtWidgets.QStyledItemDelegate):
    """
    カスタムでデリゲートをつくる
    """

    def __init__(self, parent=None):
        super(CustomTableDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        # 画像サイズとマージンの定義
        THUMB_WIDTH = 60
        # MARGIN = 5
        bgBrush = QtGui.QBrush(QtGui.QColor(43, 43, 43))
        bgPen = QtGui.QPen(QtGui.QColor(60, 60, 60), 0.5, QtCore.Qt.SolidLine)
        painter.setBrush(bgBrush)
        painter.setPen(bgPen)
        painter.drawRect(option.rect)
        # stateプロパティがセレクトがどうかチェック
        if option.state & QtWidgets.QStyle.State_Selected:
            bgBrush = QtGui.QBrush(QtGui.QColor(120, 120, 120))
            bgPen = QtGui.QPen(QtGui.QColor(60, 60, 60),
                               0.5, QtCore.Qt.SolidLine)
            painter.setPen(bgPen)
            painter.setBrush(bgBrush)
            painter.drawRect(option.rect)

        # indexからデータを取り出す
        # 画像ファイルを取ってくる
        thumbName = index.data(QtCore.Qt.UserRole)
        # パス生成
        imagePath = os.path.join(CURRENT_PATH, FOLDER, thumbName)
        # Pixmapオブジェクトに変換
        thumbImage = QtGui.QPixmap(imagePath).scaled(THUMB_WIDTH, THUMB_WIDTH)
        # 画像の表示場所を指定
        r = QtCore.QRect(option.rect.left()+(option.rect.width()-THUMB_WIDTH)/2, option.rect.top(),
                         THUMB_WIDTH, THUMB_WIDTH)
        painter.drawPixmap(r, thumbImage)

    def sizeHint(self, option, index):
        # セルのサイズ
        return QtCore.QSize(60, 60)


class OptionWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(OptionWidget, self).__init__(*args, **kwargs)
        layout = QtWidgets.QGridLayout(self)
        # QAbstractTableModelに渡すデータ作成
        data = self.createImageFileList()

        self.myListModel = CustomTableModel(data=data)
        # View作成
        self.myTableView = QtWidgets.QTableView()
        # Viewにmodelをセット
        self.myTableView.setModel(self.myListModel)
        # delegate作成
        myListDelegate = CustomTableDelegate()
        # Viewにdelegateをセット
        self.myTableView.setItemDelegate(myListDelegate)
        # delegateのsizehintを呼ぶために必要っぽい
        self.myTableView.resizeRowsToContents()
        # ヘッダーを隠す
        header = self.myTableView.horizontalHeader()
        header.hide()
        header = self.myTableView.verticalHeader()
        header.hide()

        layout.addWidget(self.myTableView, 0, 0, 1, 2)

        button = QtWidgets.QPushButton('assign', self)
        button.clicked.connect(qt.Callback(self.assign))
        layout.addWidget(button, 1, 0, 1, 2)

    def create(self):
        """選択したmatcapでマテリアルを作成する"""
        createMatcapMaterial(MATERIAL_NAME, self.getImagePath())

    def assign(self):
        """選択したmatcapでマテリアルを作成して
        選択したオブジェクトに適用する
        すでに同じ名前のマテリアルが存在するときは入れ替える
        """
        selection = cmds.ls(sl=True)
        # すでに同じ名前のマテリアルが割り当てられたオブジェクトがあるなら入れ替える
        matcap_objects = cmds.ls(sl=True)
        cmds.hyperShade(objects=MATERIAL_NAME)
        sel = cmds.ls(sl=True)
        if sel:
            matcap_objects += sel
        if not matcap_objects:
            return

        cmds.select(matcap_objects)

        mat = cmds.ls(MATERIAL_NAME)
        if mat:
            cmds.delete(mat)
            SG = mat[0]+"SG"
            print(SG)
            cmds.delete(SG)

        shader_name = createMatcapMaterial(MATERIAL_NAME, self.getImagePath())
        assignMatcapMaterial(shader_name)
        cmds.select(selection)

    def getImagePath(self):
        """GUI上で選択した画像のパスを返す"""
        # viewからindexを取得
        index = self.myTableView.currentIndex()
        # modelからデータをもらう
        thumbName = self.myListModel.data(index, QtCore.Qt.UserRole)
        imagePath = os.path.join(CURRENT_PATH, FOLDER, thumbName)
        return imagePath

    def getImageFiles(self):
        """フォルダの中身のファイルリストを返す"""
        filePath = os.path.join(CURRENT_PATH, FOLDER)
        fileList = os.listdir(filePath)
        return fileList

    def createImageFileList(self):
        """ファイルリストをマトリクスにして返す"""
        imageFiles = self.getImageFiles()
        filesMatrix = []
        temp = []
        for image in imageFiles:
            temp.append(image)
            if len(temp) == COLUMN:
                filesMatrix.append(temp)
                temp = []
        else:
            if temp:
                filesMatrix.append(temp)

        return filesMatrix


def createMatcapMaterial(material_name, matcap_image_name):
    """
    matcapのマテリアルをshaderFXから作る
    matcap_image_name : imageファイルの名前
    return : マテリアルの名前
    """
    selection = cmds.ls(sl=True)
    if not cmds.pluginInfo("shaderFXPlugin", q=True, loaded=True):
        cmds.loadPlugin("shaderFXPlugin")
        cmds.pluginInfo("shaderFXPlugin", e=True, autoload=True)

    cmds.shadingNode("ShaderfxShader", asShader=True, n=material_name)
    # shaderfxグラフを読み込む
    graph_path = os.path.join(CURRENT_PATH, "matcap_mat.sfx")

    cmds.shaderfx(sfxnode=material_name, loadGraph=graph_path)

    node_name = "TextureMap"
    node_id = cmds.shaderfx(sfx_node=material_name, getNodeIDByName=node_name)
    texture_path = os.path.join(CURRENT_PATH, "matcaps", matcap_image_name)
    # テクスチャアサイン
    cmds.shaderfx(sfxnode=material_name, edit_string=[
                  node_id, "texturepath_MyTexture", texture_path])
    cmds.select(selection)
    return material_name


def assignMatcapMaterial(shader_name):
    """選択しているオブジェクトにマテリアルを割り当てる"""
    cmds.hyperShade(assign=shader_name)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle('Matcap')
        self.resize(440, 500)

        optionWidget = OptionWidget(self)
        self.setCentralWidget(optionWidget)


def main():
    window = MainWindow(qt.getMayaWindow())
    window.show()
