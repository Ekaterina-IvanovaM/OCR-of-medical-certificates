import pandas as pd

class TableToCsv:
    
    def __init__(self:'str', path):
        self.path = path
        
    def donation_type(self, s):
        s =str(s)
        if 'бв' in s:
            return 'Безвозмездно'
        else:
            return 'Безвозмездно'
        
    
    def blood(self, s):
        s =str(s)
        if 'пл' in s:
            return 'Плазма'
        elif 'т' in s or 'т/ф' in s or 'т/' in s or 'T' in s or 'ц' in s:
            return 'Тромбоциты'
        else:
            return 'Цельная кровь'
        
        
    def read_table(self):
        self.table = pd.read_excel(self.path)
        
        
    def prep_table(self):
        if self.table.shape[1]%4 == 0 :
            if str(self.table.iloc[0][1]).isdigit() or str(self.table.iloc[0][5]).isdigit():
                self.table = self.table.drop([0], axis=0).reset_index(drop=True)
            self.table_1 = self.table.iloc[:,:4]
            self.table_1.columns = ['Дата донации', 'донации', 'Кол-во', 'Подпись']
            self.table_2=self.table.iloc[:,4:]
            self.table_2.columns = ['Дата донации', 'донации', 'Кол-во', 'Подпись']
            self.table = pd.concat([self.table_1, self.table_2], axis=0).reset_index(drop=True).drop(['Подпись'], axis=1)

            
        if self.table.shape[1]%9 == 0:
            if (str(self.table.iloc[0][1]).isdigit() or str(self.table.iloc[0][4]).isdigit() or str(self.table.iloc[0][7]).isdigit()) or \
                (str(self.table.iloc[1][1]).isdigit() or str(self.table.iloc[1][4]).isdigit() or str(self.table.iloc[1][7]).isdigit()):
                self.table = self.table.drop([0], axis=0).reset_index(drop=True)
            if (str(self.table.iloc[0][1]).isdigit() or str(self.table.iloc[0][4]).isdigit() or str(self.table.iloc[0][7]).isdigit()):
                self.table = self.table.drop([0], axis=0).reset_index(drop=True)
            self.table_1 = self.table.iloc[:,:3]
            self.table_1.columns = ['Дата донации', 'донации', 'Кол-во']
            self.table_2=self.table.iloc[:,3:6]
            self.table_2.columns = ['Дата донации', 'донации', 'Кол-во']
            self.table_3=self.table.iloc[:,6:]
            self.table_3.columns = ['Дата донации', 'донации', 'Кол-во']
            self.table = pd.concat([self.table_1, self.table_2, self.table_3], axis=0).reset_index(drop=True)
            p
    
    
    def format_table(self):
        self.t = self.table.dropna(how='all', axis=0).reset_index(drop=True)
        self.t['Дата донации'] = self.t['Дата донации'].str.replace(',', '.')
        self.t['Дата донации'] = self.t['Дата донации'].str.replace('..', '.')
        self.t['Дата донации'] = self.t['Дата донации'].str.replace(r"[^\d\.]", '.', regex=True)
        try:
            ind = pd.to_datetime(self.t['Дата донации'], format='%d.%m.%y').sort_values().index 
            self.t = self.t.iloc[ind].reset_index(drop=True)
        except:
            pass
        self.t['Класс крови'] = self.t['донации'].apply(self.blood)
        self.t['Тип донации'] = self.t['донации'].apply(self.donation_type)
        try:
            self.t['Кол-во'] = self.t['Кол-во'].astype('int')
        except:
            pass
        self.t = self.t.drop(['донации'], axis=1)
            
            
            
    def save_csv(self):
        self.t.to_csv('result/csv_table.csv', index=False)
            
    def result(self):
        self.read_table()
        self.prep_table()
        self.format_table()
        self.save_csv()