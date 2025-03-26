"""
Table models module for the Spring Test App.
Contains Qt table models for displaying data in the UI.
"""
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QColor, QBrush, QFont


class PandasModel(QAbstractTableModel):
    """Model for displaying pandas DataFrame in QTableView"""
    
    def __init__(self, data: pd.DataFrame):
        super().__init__()
        self._data = data
        self._header_font = QFont()
        self._header_font.setBold(True)
        
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        return self._data.shape[0]

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the model."""
        return self._data.shape[1]

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> QVariant:
        """Return the data at the given index."""
        if not index.isValid():
            return QVariant()
            
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)
            
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
            
        if role == Qt.BackgroundRole:
            # Alternate row colors for better readability
            if index.row() % 2 == 0:
                return QBrush(QColor(240, 240, 240))
            
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> QVariant:
        """Return the header data."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return str(self._data.columns[section])
            
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(section + 1)
            
        if role == Qt.FontRole:
            return self._header_font
            
        return QVariant()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Return the item flags for the given index."""
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Sort the model by the given column."""
        self.layoutAboutToBeChanged.emit()
        self._data = self._data.sort_values(
            by=self._data.columns[column],
            ascending=(order == Qt.AscendingOrder)
        )
        self.layoutChanged.emit()
    
    def update_data(self, data: pd.DataFrame) -> None:
        """Update the model data."""
        self.layoutAboutToBeChanged.emit()
        self._data = data
        self.layoutChanged.emit()


class CommandTableModel(QAbstractTableModel):
    """Model for displaying command reference data"""
    
    def __init__(self, commands: Dict[str, str]):
        super().__init__()
        self.commands = [(k, v) for k, v in commands.items()]
        self.headers = ["Command", "Description"]
        self._header_font = QFont()
        self._header_font.setBold(True)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        return len(self.commands)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the model."""
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> QVariant:
        """Return the data at the given index."""
        if not index.isValid():
            return QVariant()
            
        if role == Qt.DisplayRole:
            return self.commands[index.row()][index.column()]
            
        if role == Qt.TextAlignmentRole:
            # Align command names to the center-left and descriptions to the left
            if index.column() == 0:  # Command column
                return Qt.AlignCenter
            else:  # Description column
                return Qt.AlignLeft | Qt.AlignVCenter
                
        if role == Qt.BackgroundRole:
            # Alternate row colors for better readability
            if index.row() % 2 == 0:
                return QBrush(QColor(240, 240, 240))
                
        if role == Qt.FontRole and index.column() == 0:
            # Make command names bold
            font = QFont()
            font.setBold(True)
            return font
            
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> QVariant:
        """Return the header data."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
            
        if role == Qt.FontRole:
            return self._header_font
            
        return QVariant()
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Sort the model by the given column."""
        self.layoutAboutToBeChanged.emit()
        self.commands.sort(
            key=lambda x: x[column],
            reverse=(order != Qt.AscendingOrder)
        )
        self.layoutChanged.emit()


class HistoryTableModel(QAbstractTableModel):
    """Model for displaying sequence history"""
    
    def __init__(self, sequences: List[Dict[str, Any]]):
        super().__init__()
        self.sequences = sequences
        self.headers = ["Name", "Parameters", "Created", "Actions"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        return len(self.sequences)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns in the model."""
        return len(self.headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> QVariant:
        """Return the data at the given index."""
        if not index.isValid():
            return QVariant()
            
        if role == Qt.DisplayRole:
            sequence = self.sequences[index.row()]
            if index.column() == 0:  # Name
                return sequence.get("name", f"Sequence {index.row()+1}")
            elif index.column() == 1:  # Parameters
                # Show key parameters
                params = sequence.get("parameters", {})
                if "Free Length" in params:
                    return f"Length: {params['Free Length']}mm"
                elif "Part Number" in params:
                    return f"Part: {params['Part Number']}"
                else:
                    return "No parameters"
            elif index.column() == 2:  # Created
                created = sequence.get("created_at", "")
                if isinstance(created, str):
                    # Return just the date part if it's in ISO format
                    if "T" in created:
                        return created.split("T")[0]
                return created
            elif index.column() == 3:  # Actions
                return "Load"
                
        if role == Qt.TextAlignmentRole:
            if index.column() == 3:  # Actions column
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
            
        if role == Qt.BackgroundRole:
            # Alternate row colors for better readability
            if index.row() % 2 == 0:
                return QBrush(QColor(240, 240, 240))
                
        return QVariant()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> QVariant:
        """Return the header data."""
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return QVariant()
    
    def add_sequence(self, sequence: Dict[str, Any]) -> None:
        """Add a sequence to the model."""
        self.layoutAboutToBeChanged.emit()
        self.sequences.append(sequence)
        self.layoutChanged.emit()
    
    def remove_sequence(self, index: int) -> None:
        """Remove a sequence from the model."""
        if 0 <= index < len(self.sequences):
            self.layoutAboutToBeChanged.emit()
            del self.sequences[index]
            self.layoutChanged.emit()
    
    def get_sequence(self, index: int) -> Optional[Dict[str, Any]]:
        """Get a sequence from the model."""
        if 0 <= index < len(self.sequences):
            return self.sequences[index]
        return None 