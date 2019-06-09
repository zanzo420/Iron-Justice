import discord
from utils.utils import createEmbed
from datetime import datetime
#import mysql


class Storage:
    
    def __init__(self):
        self.conn = None
        '''
        self.conn = mysql.connector.connect(
            host="localhost",
            user=Configuration.DBUsername,
            passwd=Configuration.DBPassword,
            database=Configuration.DBName
        )'''
        self.datetime_scheme = '%Y-%m-%d %H:%M:%S'

    
    def get_cursor(self):
        try:
            cursor = self.conn.cursor()
            return cursor
        except Exception as e:
            raise e

    def execute_query(self, query: str, commit: bool = False):
        cur = self.get_cursor()
        cur.execute(query)
        if commit:
            self.conn.commit()
        r = cur.fetchone()
        cur.close()
        return r

    def execute_query_many(self, query: str, commit: bool = False):
        cur = self.get_cursor()
        cur.execute(query)
        if commit:
            self.conn.commit()
        r = cur.fetchall()
        cur.close()
        return r


    '''
        CLEAN UP AND GENERAL FUNCTIONS
    '''


    def add_server(self, guild: discord.Guild):
        query = f'INSERT INTO settings (gid) VALUES ({guild.id})'
        self.execute_query(query, commit=True)


    def guild_leave(self, guild: discord.Guild):
        query = f'DELETE FROM messages WHERE gid={guild.id};'
        self.execute_query(query)
        #TODO add more queries for cleanup

    '''
        PROFILE FUNCTIONS
    '''

    async def get_sot_profile(self, ctx, user: discord.Member):
        query = f'SELECT hc,sd,gh,oos,ma,af,img,alias FROM sot_profile WHERE uid={user.id};'
        r = self.execute_query(query)

        #If Profile doesn't exist yet
        if r.rowcount == 0:
            await self.create_profile(ctx, user)
            return

        profile = {
            'hc': r[0],
            'sd': r[1],
            'gh': r[2],
            'oos': r[3],
            'ma': r[4],
            'af': r[5],
            'img': r[6],
            'alias': r[7],
        }
        profile['gtag'] = self.get_xbox_tag(user)
        return profile

    def get_tag_profile(self, user: discord.Member):
        query = f'SELECT steam,xbox,psn,nintendo FROM gamertags WHERE uid={user.id};'
        r = self.execute_query(query)[0]
        profile = {
            'steam': r[0],
            'xbox': r[1],
            'psn': r[2],
            'nintendo': r[3],
        }
        return profile

    def get_xbox_tag(self, user: discord.Member):
        query = f'SELECT xbox FROM gamertags WHERE uid={user.id};'
        r = self.execute_query(query)
        return r[0]

    async def create_profile(self, ctx, user: discord.Member):
        query = f'INSERT INTO sot_profile (uid) VALUES ({user.id});'
        self.execute_query(query)                                                #CAN I ONLY COMMIT ONCE?
        query = f'INSERT INTO gamertags (uid) VALUES ({user.id});'
        self.execute_query(query, commit=True)

        embed = createEmbed(title='**__Profile Created__**', colour='iron', author=user)
        embed.add_field(name="__add your information__", value="1. Add your XBox gamertag with `?gt edit <gamertag>`.\n2. Add your levels with `?levels gh=<gh> oos=<oos>` etc... Use `?help levels` for more info.", inline=False)
        embed.add_field(name="__optional features__", value="- Add an image of your pirate with `?set_image <URL>`. You can also upload the image right to discord and type `?set_image` without any paramters.\nThis URL **NEEDS** to be a direct link to the image ending with `.jpg`, `.png` or `.gif`.\n- Add a pirate name (for role players) by typing `?alias <piratename>`.", inline=False)
        embed.add_field(name="__additional notes__", value="Please note that you **DO NOT** need to add the brackets (`<>`, `[]`). They are merely Syntax to show which arguments are mandatory (`<>`) and which can be left out and will use the previous value (`[]`). This is programming standard.", inline=False)
        await ctx.send(embed=embed)

    def update_levels(self, user: discord.Member, comps: dict(str, int)):
        cur = self.get_cursor()
        cur.executemany(f'UPDATE sot_profile SET %s=%s WHERE uid={user.id};', comps.items())
        self.conn.commit()
        cur.close()

    def update_gamertag(self, user: discord.Member, platform: str, gamertag: str):
        query = f'UPDATE gamertags SET {platform}=\'{gamertag}\' WHERE uid={user.id};'
        self.execute_query(query, commit=True)

    def update_img(self, user: discord.Member, url: str):
        query = f'UPDATE sot_profile SET img=\'{url}\' WHERE uid={user.id};'
        self.execute_query(query, commit=True)
    
    def remove_img(self, user:discord.Member):
        query = f'UPDATE sot_profile SET img=NULL WHERE uid={user.id};'
        self.execute_query(query, commit=True)
        
    def update_alias(self, user: discord.Member, alias: str):
        query = f'UPDATE sot_profile SET alias=\'{alias}\' WHERE uid={user.id};'
        self.execute_query(query, commit=True)

    def remove_alias(self, user: discord.Member):
        query = f'UPDATE sot_profile SET alias=NULL WHERE uid={user.id};'
        self.execute_query(query, commit=True)

    '''
        `LOOKING FOR CREW`-MODULE SETTINGS
    '''

    def get_lfc_settings(self, guild: discord.Guild):
        settings = dict()
        query = f'SELECT lfc FROM settings WHERE gid={guild.id};'
        settings['status'] = self.execute_query(query)[0]
        query = 'SELECT cid FROM lfc_channels WHERE gid={guild.id};'
        r = self.execute_query_many(query)
        settings['channels'] = [guild.get_channel(c[0]) for c in r]
        return settings
        
    def update_lfc_status(self, guild: discord.Guild, status: bool):
        query = f'UPDATE settings SET lfc={str(status)} WHERE gid={guild.id};'
        self.execute_query(query, commit=True)

    def add_lfc_channels(self, guild: discord.Guild, channels: list(discord.abc.GuildChannel)):
        cur = self.get_cursor()
        cur.executemany(f'INSERT INTO lfc_channels (cid,gid) VALUES (%s,{guild.id});', channels)
        self.conn.commit()
        cur.close()

    def delete_all_lfc_channels(self, guild: discord.Guild):
        query = f'DELETE FROM lfc_channels WHERE gid={guild.id};'
        self.execute_query(query, commit=True)

    '''
        `PROFILE`-MODULE SETTINGS
    '''

    def get_profile_settings(self, guild: discord.Guild):
        settings = dict()
        query = f'SELECT profile FROM settings WHERE gid={guild.id};'
        settings['status'] = self.execute_query(query)[0]
        query = f'SELECT cid FROM profile_channels WHERE gid={guild.id};'
        r = self.execute_query_many(query)
        settings['channels'] = [guild.get_channel(c[0]) for c in r]
        return settings

    def update_profile_status(self, guild:discord.Guild, status: bool):
        query = f'UPDATE settings SET profile={str(status)} WHERE gid={guild.id};'
        self.execute_query(query, commit=True)

    def add_profile_channels(self, guild: discord.Guild, channels: list(discord.abc.GuildChannel)):
        cur = self.get_cursor()
        cur.executemany(f'INSERT INTO profile_channels (cid,gid) VALUES (%s,{guild.id});', channels)
        self.conn.commit()
        cur.close()

    def delete_all_profile_channels(self, guild: discord.Guild):
        query = f'DELETE FROM profile_channels WHERE gid={guild.id};'
        self.execute_query(query, commit=True)

    '''
        `AUTO-VOICE`-MODULE SETTINGS
    '''

    def get_auto_voice_settings(self, guild:discord.Guild):
        settings = dict()
        query = f'SELECT auto_voice_channel FROM settings WHERE gid={guild.id};'
        r = self.execute_query(query)[0]
        settings['auto_voice_channel'] = guild.get_channel(r)
        settings['names'] = self.get_auto_voice_names(guild)
        return settings

    def get_auto_voice_names(self, guild:discord.Guild):
        query = f'SELECT name FROM auto_voice_names WHERE gid={guild.id};'
        r = self.execute_query_many(query)
        return [n[0] for n in r]


    def update_auto_voice_channel(self, guild:discord.Guild, channel: discord.abc.GuildChannel):
        query = f'UPDATE settings SET auto_voice_channel={channel.id} WHERE gid={guild.id};'
        self.execute_query(query, commit=True)
    
    def add_auto_voice_names(self, guild:discord.Guild, names: list(str)):
        cur = self.get_cursor()
        cur.executemany(f'INSERT INTO auto_voice_names (name,gid) VALUES (\'%s\',{guild.id});', names)
        self.conn.commit()
        cur.close()

    def delete_auto_voice_names(self, guild:discord.Guild, names: list(str)):
        cur = self.get_cursor()
        cur.executemany(f'DELETE FROM auto_voice_names WHERE name=\'%s\' and gid={guild.id};', names)
        self.conn.commit()
        cur.close()

    def delete_all_auto_voice_names(self, guild:discord.Guild):
        query = f'DELETE FROM auto_voice_names WHERE gid={guild.id};'
        self.execute_query(query, commit=True)


    '''
        `ACTIVITY-LOGGING` SETTINGS
    '''

    def get_activity_logging_status(self, guild: discord.Guild):
        query = f'SELECT activity_logging FROM settings WHERE gid={guild.id}'
        r = self.execute_query(query)[0]
        return r        

    def update_activity_logging_status(self, guild:discord.Guild, status: bool):
        query = f'UPDATE settings SET activity_logging={str(status)} WHERE gid={guild.id}'
        self.execute_query(query, commit=True)

    '''
        `ACTIVITY-LOGGING` FUNCTIONS
    '''

    def cleanup_messages(self, guilds:list(discord.Guild)):
        cur = self.get_cursor()
        query = f'DELETE FROM messages WHERE datetime < DATE_SUB(NOW(), INTERVAL 30 DAY) OR gid NOT IN ({",".join(g.id for g in guilds)});'
        cur.execute(query)
        self.conn.commit()
        count = cur.rowcount
        cur.close()
        return count

    def user_leave(self, user:discord.Member):
        query = f'DELETE FROM messages WHERE aid={user.id} and gid={user.guild.id};'
        self.execute_query(query, commit=True)

    def add_message(self, m: discord.Message):
        timestamp = m.created_at.strftime(self.datetime_scheme)
        query = f'INSERT INTO messages (mid,aid,gid,timestamp) VALUES({m.id},{m.author.id},{m.guild.id},{timestamp};'
        self.execute_query(query, commit=True)

    def get_user_activity(self, user:discord.Member):
        info = dict()
        query = f'SELECT COUNT(*) FROM messages WHERE aid={user.id} AND gid={user.guild.id}'
        info['amnt'] = self.execute_query(query)[0]
        query = f'SELECT datetime FROM messages WHERE aid={user.id} AND gid={user.guild.id} ORDER BY datetime DESC LIMIT 1'
        timestamp = self.execute_query(query)[0]
        info['timestamp'] = datetime.strptime(timestamp, self.datetime_scheme)
        return info
