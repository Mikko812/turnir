import pandas as pd
import json

null_list = [0]*8
cols = ['id', 'игра1', 'игра2', 'игра3', 'игра4', 'Гандикап', 'Сумма', 'Итог']
keys_json = ['id', 'игрок', 'игра1', 'игра2', 'игра3', 'игра4', 'Гандикап', 'Сумма', 'Итог']
table = pd.DataFrame(columns=cols)


def db_to_df(db):
    global table
    table = pd.DataFrame(columns=cols)
    if len(db) > 0:
        for i, c in enumerate(cols[1:]):
            table[c] = [x[i+2] for x in db]
        table['id'] = [x[0] for x in db]
        table.index = [x[1] for x in db]
    print(table)
    save_json(db)


def save_json(db):
    table_json = {}
    for el in db:
        tmp = {}
        for c in range(len(keys_json)):
            tmp[keys_json[c]] = el[c]
        table_json[el[0]] = tmp
    with open(r'table.json', 'w') as f:  # D:\PyCharmPrj\flask_test\
        json.dump(table_json, f)
        print('Таблица обновлена!')


def add_result(name: str, result: int):
    print(table)
    curr_res = list(table.loc[name])
    game_num = curr_res.index(0) + 1
    if game_num < 5:
        table.loc[name, f'игра{game_num}'] = result
        curr_res = list(table.loc[name])
        summa = sum(curr_res[:game_num])
        itog = summa + curr_res[4] * game_num
        table.loc[name, 'Сумма'] = summa
        table.loc[name, 'Итог'] = itog
        print(table)
        return round(table.loc[name, :'игра4'].mean(), 2) \
            if game_num == 4 else round(table.loc[name, :f'игра{game_num}'].mean(), 2)
    else:
        return 0
