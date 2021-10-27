import asyncio
import json
import random
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_choice, create_option


token = ""


botID = 884522374370840646
start_msg = ""
msg_author = ""
inhouse_members = []
watchers = []
channel_name = ""
copy_list = []
logs = []
game_started = False

first_use = True

guilds = [357304558214447156,752060071839793162,874057796361015327]

bot = commands.Bot(command_prefix="!")
slash = SlashCommand(bot, sync_commands=True)


@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

@slash.slash(
    name="queue",
    description="Starts in-house waiting room!",
    guild_ids= guilds
)
async def _queue(ctx:SlashContext):
    global start_msg
    global msg_author
    global channel_name
    global inhouse_members
    
    inhouse_members.clear

    voice_state = ctx.author.voice
    if voice_state is None:
        return await ctx.send("You need to be in a voice channel to use this command!")
    
    channel_name= voice_state.channel.name
    userID = ctx.author_id
    embed = discord.Embed(
        title = "React to this message to join the in-house waiting room!",
        description = "Only those in " + str(channel_name) + " voice chat can react!\n\nReact with ✅ to join!\nReact with 👁️ if you're just watching!"
    )
    msg = await ctx.send(embed=embed)
    start_msg = msg.id
    msg_author = ctx.author
    await msg.add_reaction("✅")
    await msg.add_reaction("👁️")
    
    
    
#TODO: Actually divide up members, one last check that those participating are still in vc, then team division

@slash.slash(name="begin",description="Start the inhouse! Use this when everyone is ready from /queue!", guild_ids=guilds, options=[
    create_option(
        name="contact",
        description="Contact ID (ex: ExampleRiotID#NA1)",
        required=True,
        option_type=3
    ),
    create_option(
        name="automove",
        description="Automatically moves players in 10 seconds if true",
        required=True,
        option_type=5
    ),
    create_option(
        name="party_size",
        description="Specify how large the party will be (e.g. for 5v5, size 10)",
        required=True,
        option_type=4
    )
])
async def _begin(ctx:SlashContext,contact:str,automove:bool,party_size:int):
    global inhouse_members
    global copy_list
    global first_use
    global logs
    global game_started

    if first_use:
        copy_list = inhouse_members
        first_use = False

    

    #Weirdly inefficient process of checking if user has Spartan Gaming roles 
    inhouse_role = False
    roles = ctx.author.roles

    for role in roles:
        if role.name == 'Event Coordinators' or role.name == 'Discord Mod' or role.name == 'Discord Moderator' or role.name == 'Officers':
            inhouse_role = True
            break

    if msg_author == ctx.author or inhouse_role: #Queue author is the one that uses begin
        channel = ctx.channel
        voice = ctx.author.voice.channel
        await ctx.send("Add **" + str(contact) + "** for the inhouse!")

        #Randomizing teams
        random.shuffle(copy_list)
        team_size = party_size
        #Successful game creation
        if(len(copy_list)>=team_size): #Team Size 
            game_started = True
            if automove:
                msg = await bot.get_channel(channel.id).send("Moving participants in 5 seconds!") 
                await asyncio.sleep(5)
                await msg.edit(content="Moving participants now!")
                await asyncio.sleep(1)
                for x in range(team_size):
                        await copy_list[0].move_to(voice)
                        logs.append(copy_list[0])
                        copy_list.remove(copy_list[0])
            else:
                member_str = ""
                for i in copy_list:
                    member_str += str(i.display_name) + " "
                    logs.append(str(i.display_name))
                    copy_list.remove(copy_list[0])
                await bot.get_channel(channel.id).send(str(member_str))
        #Unsuccessful game creation        
        else: 
            unlucky_players = ""
            for i in range(0, len(copy_list)):
                if i == 0:
                    unlucky_players = str(copy_list[i])
                elif i == (len(copy_list)-1):
                    unlucky_players += " and " + str(copy_list[i]) + ""
                else:
                    unlucky_players += str(copy_list[i]) + ", "
            if game_started:
                await bot.get_channel(channel.id).send("Not enough members to make another team! I looks like " + str(unlucky_players) + " is/are spectating!")
                
            else:
                await bot.get_channel(channel.id).send("Not enough players available to start a game!")
                

    else:
        try:
            await ctx.send("Hold on <@" + str(ctx.author_id) + ">! Only <@" + str(msg_author.id) + "> or an inhouse officer can start the inhouse!")
        except AttributeError:
            pass
    
def divide_chunks(l:list,n:int):
    #looping til length l
    for i in range(0,len(l),n):
        yield l[i:i+n]



@bot.event
async def on_raw_reaction_add(payload):
    if(payload.message_id == start_msg):
        if(payload.member.id != botID):
            guild = await(bot.fetch_guild(payload.guild_id))
            member = await(guild.fetch_member(payload.user_id))
            if(payload.emoji.name == "✅"):
                if(payload.member.voice.channel.name == channel_name):
                    inhouse_members.append(member)
                else:
                    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                    await message.remove_reaction("✅", member)
                    await member.send("Hello! If you're looking to join the in-house waiting room be sure to be in **" + str(channel_name) + "** voice channel!")
            elif(payload.emoji.name == "👁️"):
                watchers.append(member)
                
@bot.event
async def on_raw_reaction_remove(payload):
    if(payload.message_id == start_msg):
        guild = await(bot.fetch_guild(payload.guild_id))
        member = await(guild.fetch_member(payload.user_id))
        if(member != botID):
            if(payload.emoji.name == "✅"):
                if member is not None:
                    try:
                        inhouse_members.remove(member)
                    except ValueError:
                        pass
            elif(payload.emoji.name == "👁️"):
                if member is not None:
                    try:
                        watchers.remove(member)
                    except ValueError:
                        pass
@bot.command
async def get_members(ctx):
    await ctx.send(inhouse_members)

bot.run(token)
