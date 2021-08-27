import sqlite3 as sql


class SqlDb:
    """Метод, создающий соединение с базой данных, либо новую базу данных(при её отсутствии по пути path_name)"""
    def __init__(self, bd_name):
        self.connect = sql.connect(bd_name, check_same_thread=False)
        self.cursor = self.connect.cursor()
        self.bd_name = bd_name[:-3]
        if 'turnir' in self.bd_name:
            self.cursor.execute(
                f'''CREATE TABLE IF NOT EXISTS {self.bd_name} (
                id INT PRIMARY KEY,
                name TEXT, 
                g1 INT, 
                g2 INT, 
                g3 INT, 
                g4 INT, 
                handikap INT,
                summa INT,
                itog INT,
                id2 INT)
                ''')
        else:
            self.cursor.execute(f'CREATE TABLE IF NOT EXISTS {self.bd_name} '
                                f'(id INT PRIMARY KEY, name TEXT, handikap INT)')
        self.connect.commit()

    def add_new_player_in_db(self, data: tuple):
        with self.connect:
            if self.bd_name == 'players':
                if data[0] == 0:
                    self.cursor.execute(f'SELECT count(*) FROM {self.bd_name} WHERE id<100;')
                    none_telegram_players = self.cursor.fetchall()[0][0] + 1
                    data = (none_telegram_players, data[1], data[2])
                self.cursor.execute('INSERT INTO players VALUES (?, ?, ?);', data)
                self.connect.commit()
                print(f'Игрок {data[1]} добавлен в общую БД.')
            else:
                self.cursor.execute(f'SELECT max(id) FROM {self.bd_name}')
                players_count = self.cursor.fetchone()[0]
                if not players_count:
                    players_count = 1
                else:
                    players_count += 1
                player_id = data[0]
                print(player_id)
                data = (players_count, data[1], data[2], player_id)
                self.cursor.execute(f'INSERT INTO {self.bd_name} VALUES (?, ?, 0, 0, 0, 0, ?, 0, 0, ?);', data)
                self.connect.commit()
                print(f'Игрок {data[1]} добавлен в БД турнира.')

    def add_result_in_db(self, player_id, result):
        with self.connect:
            if player_id > 100:
                self.cursor.execute(f'SELECT * FROM {self.bd_name} WHERE id2=?;', [player_id])
                player_id = self.cursor.fetchone()[0]
            self.cursor.execute(f'SELECT * FROM {self.bd_name} WHERE id=?;', [player_id])
            player = list(self.cursor.fetchone())
            pos = player.index(0) - 1
            if pos < 5:
                self.cursor.execute(f'UPDATE {self.bd_name} SET g{str(pos)}={result} WHERE id={player_id}')
                summa = sum(player[2:pos+1] + [int(result)])
                itog = summa + player[6] * pos
                self.cursor.execute(f'UPDATE {self.bd_name} SET summa={summa} WHERE id={player_id}')
                self.cursor.execute(f'UPDATE {self.bd_name} SET itog={itog} WHERE id={player_id}')
                self.connect.commit()
                return round(itog/pos, 2)
            return 0

    def change_result_in_db(self, player_id, game, result):
        with self.connect:
            self.cursor.execute(f'SELECT * FROM {self.bd_name} WHERE id=?;', [player_id])
            player = list(self.cursor.fetchone())
            player[int(game) + 1] = result
            handikap = player[8] - player[7]
            summa = sum(player[2:6])
            itog = summa + handikap
            self.cursor.execute(f'UPDATE {self.bd_name} SET g{str(game)}={result} WHERE id={player_id}')
            self.cursor.execute(f'UPDATE {self.bd_name} SET summa={summa} WHERE id={player_id}')
            self.cursor.execute(f'UPDATE {self.bd_name} SET itog={itog} WHERE id={player_id}')
            self.connect.commit()

    def remove_player_from_turnir(self, player_id):
        with self.connect:
            self.cursor.execute(f'DELETE FROM {self.bd_name} WHERE id={player_id}')
            self.connect.commit()

    def convert_db_to_df(self):
        with self.connect:
            self.cursor.execute(f'SELECT * FROM {self.bd_name}')
        return self.cursor.fetchall()

    def get_player_by_id(self, player_id):
        with self.connect:
            self.cursor.execute(f'SELECT * FROM {self.bd_name} WHERE id={player_id}')
            pl_name = self.cursor.fetchone()
        if pl_name is None:
            return None
        return pl_name[1]

    def get_player_by_name(self, player_name):
        with self.connect:
            self.cursor.execute(f'SELECT * FROM {self.bd_name} WHERE name=?;', [player_name])
            pl_id = self.cursor.fetchone()
        if pl_id is None:
            return None
        return pl_id[0]

    def get_results(self, player_id):
        with self.connect:
            self.cursor.execute(f'SELECT * FROM {self.bd_name} WHERE id2={player_id}')
            res = list(self.cursor.fetchone()[2:6])
            pos = 4
            if 0 in res:
                pos = res.index(0)
            res = [str(x) for x in res]
            return ', '.join(res[:pos])

    def save_handikap(self, player_id, handikap):
        with self.connect:
            self.cursor.execute(f'UPDATE {self.bd_name} SET handikap={handikap} WHERE id={player_id}')
            self.connect.commit()

    def get_all_players(self):
        with self.connect:
            self.cursor.execute(f'SELECT * FROM {self.bd_name}')
            players = self.cursor.fetchall()
        players = [f'{x[0]}. {x[1]}' for x in players]
        return players
        # return ' | '.join(players)

    def close(self):
        self.connect.close()
