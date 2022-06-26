import math
import json
import aiohttp
import discord
import requests
from time import sleep
from bs4 import BeautifulSoup
from redbot.core import commands, Config, checks
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu


async def shorten(self, magnet: str):
    res = False
    async with aiohttp.ClientSession() as session:
        async with session.get("http://mgnet.me/api/create?&format=json&opt=&m={}".format(magnet)) as response:
            res = await response.read()
    print(res)
    res = json.loads(res)
    return res["shorturl"]

class rarbg(commands.Cog):
    """
    Search Rarbg.
    """

    def __init__(self, bot):
        self.bot = bot
        self.conf = Config.get_conf(self, identifier="UNIQUE_ID", force_registration=True)
        self.conf.register_channel(rarbg_smartlink_enabled=False)
        self.conf.register_guild(rarbg_token="")

    @commands.group(aliases=["r"])
    @commands.guild_only()
    async def rarbg(self, ctx):
        """Search Rarbg"""

    @rarbg.command(aliases=["quicksearch", "q", "qs", "quicklookup", "ql"])
    async def quick(self, ctx, *, query: str):
        try:
            def format_bytes(size):
                # 2**10 = 1024
                power = 2**10
                n = 0
                power_labels = {0 : '', 1: 'Kb', 2: 'Mb', 3: 'GB', 4: 'Tb'}
                while size > power:
                    size /= power
                    n += 1
                return (str(math.ceil(size)) + " " + power_labels[n])

            async with ctx.typing():
                results = await self.rarbg_search(query, ctx.guild)
                if not len(results): return await ctx.send(f"Sorry, no results for **{query}**")
                print(results)
                format = []
                for i, res in enumerate(results):
                    if i > 9: break
                    print(res['download'])
                    format.append(f"""
                    **{i+1}. [{res['title']}]({res['info_page']})**
                    **[Magnet]({await shorten(self, res["download"])})** | Seeders: {res['seeders']} | Size: {format_bytes(res['size'])} 
                    """)

                embed = discord.Embed(
                    description="".join(format)
                )
                embed = embed.set_author(
                        name=ctx.author.display_name,
                        icon_url=ctx.author.avatar_url
                )

                await ctx.send(content="", embed=embed)
            
        except AttributeError:
            await ctx.send(f"Sorry, no results for **{query}** or there was an error.")


    async def rarbg_search(self, query, guild, **kwargs):
        """
        Return a list of dicts with the results of the query.
        """

        token = kwargs.get("token", False)
        if not token:
            token = await self.conf.guild(guild).rarbg_token()

        print(token)
        r = requests.get(f"https://torrentapi.org/pubapi_v2.php?mode=search&search_string={query}&token={token}&app_id=torrent-api&format=json_extended&sort=seeders").json()
        print(r)
        
        if len(r.keys()) > 1:
            if r['error_code'] == 20: return []

            print("Getting new token")
            new_token = requests.get("https://torrentapi.org/pubapi_v2.php?get_token=get_token&app_id=torrent-api").json()['token']
            print(f"New token: {new_token}")
            token = await self.conf.guild(guild).rarbg_token.set(new_token)
            sleep(3)
            return await self.rarbg_search(query, guild, token=token)

        else:
            return r['torrent_results']