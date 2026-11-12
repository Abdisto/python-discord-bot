import discord
from discord.ext import commands
from discord.commands import Option
import pomice

from .player import Player

class Filter(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    filter = discord.SlashCommandGroup('filter', 'Adding filters to the music bot')
    general = filter.create_subgroup('general', 'general filter options')

    @general.command(
        name='option',
        description='Manage filters for audio playback.',
    )
    @discord.option(
        name='options',
        description='add or remove filters',
        type=str,
        choices=['remove_all', 'list_active']
    )
    async def general(self, ctx, options: str) -> None:
        self.bot.logger.info(self.bot.format(options, 'Provided mode: '))
        player: Player = ctx.voice_client

        if options.lower() == 'remove_all':
            await player.reset_filters()
            await ctx.respond('Removed all filters', delete_after=5)

        elif options.lower() == 'list_active':
            # Logic to list active filters can be added here
            await ctx.respond('Active filters...', delete_after=5)

        else:
            await ctx.respond('Invalid filter option...', delete_after=5)

    @filter.command(
        name='channelmix',
        description='Adjusts stereo panning of a track.',
        options=[
            Option(name='left_to_left', description='Left to left mix.', type=float, default=1.0),
            Option(name='left_to_right', description='Left to right mix.', type=float, default=0.0),
            Option(name='right_to_left', description='Right to left mix.', type=float, default=0.0),
            Option(name='right_to_right', description='Right to right mix.', type=float, default=1.0),
        ]
    )
    async def channelmix(self, ctx, left_to_left: float, left_to_right: float, right_to_left: float, right_to_right: float) -> None:
        pomice_filter = pomice.filters.ChannelMix(tag='ChannelMix', left_to_left=float(left_to_left), left_to_right=float(left_to_right), right_to_left=float(right_to_left), right_to_right=float(right_to_right))
        player: Player = ctx.voice_client
        await player.add_filter(pomice_filter, fast_apply=True)
        await ctx.respond('ChannelMix filter applied', delete_after=5)

    @filter.command(
        name='distortion',
        description='Applies distortion to the track.',
        options=[
            Option(name='sin_offset', description='Sin offset value.', type=float, default=0.0),
            Option(name='sin_scale', description='Sin scale value.', type=float, default=1.0),
            Option(name='cos_offset', description='Cos offset value.', type=float, default=0.0),
            Option(name='cos_scale', description='Cos scale value.', type=float, default=1.0),
            Option(name='tan_offset', description='Tan offset value.', type=float, default=0.0),
            Option(name='tan_scale', description='Tan scale value.', type=float, default=1.0),
            Option(name='offset', description='Overall offset value.', type=float, default=0.0),
            Option(name='scale', description='Overall scale value.', type=float, default=1.0),
        ]
    )
    async def distortion(self, ctx, sin_offset: float, sin_scale: float, cos_offset: float, cos_scale: float,
                         tan_offset: float, tan_scale: float, offset: float, scale: float) -> None:
        pomice_filter = pomice.filters.Distortion(tag='distortion', sin_offset=float(sin_offset), sin_scale=float(sin_scale), cos_offset=float(cos_offset), cos_scale=float(cos_scale), tan_offset=float(tan_offset), tan_scale=float(tan_scale), offset=float(offset), scale=float(scale))
        player: Player = ctx.voice_client
        await player.add_filter(pomice_filter, fast_apply=True)
        await ctx.respond('Distortion filter applied', delete_after=5)

    @filter.command(
        name='equalizer',
        description='Adjusts the 15 band equalizer.',
        options=[
            Option(name='bands', description='Comma-separated gain values for each band (0 to 14).', type=str),
        ]
    )
    async def equalizer(self, ctx, bands: str) -> None:
        # Expecting input as a comma-separated string of floats
        try:
            band_gains = [float(gain.strip()) for gain in bands.split(',')]
            if len(band_gains) != 15:
                raise ValueError('Exactly 15 band gains are required.')
            pomice_filter = pomice.filters.Equalizer(tag='eq', *band_gains)
            player: Player = ctx.voice_client
            await player.add_filter(pomice_filter, fast_apply=True)
            await ctx.respond('Equalizer filter applied', delete_after=5)
        except ValueError as e:
            await ctx.respond(f'Invalid input: {str(e)}', delete_after=5)

    @filter.command(
        name='karaoke',
        description='Filters vocals from the track.',
        options=[
            Option(name='level', description='Level of the filter.', type=float, default=1.0),
            Option(name='mono_level', description='Mono level of the filter.', type=float, default=1.0),
            Option(name='filter_band', description='Filter band for the karaoke effect.', type=float, default=220.0),
            Option(name='filter_width', description='Width of the filter band.', type=float, default=100.0),
        ]
    )
    async def karaoke(self, ctx, level: float, mono_level: float, filter_band: float, filter_width: float) -> None:
        pomice_filter = pomice.filters.Karaoke(tag='karaoke', level=float(level), mono_level=float(mono_level), filter_band=float(filter_band), filter_width=float(filter_width))
        player: Player = ctx.voice_client
        await player.add_filter(pomice_filter, fast_apply=True)
        await ctx.respond('Karaoke filter applied', delete_after=5)

    @filter.command(
        name='lowpass',
        description='Applies a low pass filter to the track.',
        options=[
            Option(name='smoothing', description='Smoothing amount for the filter.', type=float, default=20.0),
        ]
    )
    async def lowpass(self, ctx, smoothing: float) -> None:
        pomice_filter = pomice.filters.LowPass(tag='lowpass', smoothing=float(smoothing))
        player: Player = ctx.voice_client
        await player.add_filter(pomice_filter, fast_apply=True)
        await ctx.respond('LowPass filter applied', delete_after=5)

    @filter.command(
        name='rotation',
        description='Produces a stereo-like panning effect.',
        options=[
            Option(name='rotation_hz', description='Rotation speed in Hz.', type=float, default=5.0),
        ]
    )
    async def rotation(self, ctx, rotation_hz: float) -> None:
        pomice_filter = pomice.filters.Rotation(tag='rotation', rotation_hz=float(rotation_hz))
        player: Player = ctx.voice_client
        await player.add_filter(pomice_filter, fast_apply=True)
        await ctx.respond('Rotation filter applied', delete_after=5)

    @filter.command(
        name='timescale',
        description='Adjusts the speed and pitch of a track or apply the nightcore preset.',
        options=[
            Option(
                name='preset',
                description='Choose a preset to apply',
                type=str,
                choices=['custom', 'nightcore'],
                required=False,
                default='custom'
            ),
            Option(
                name='speed',
                description='Playback speed.',
                type=float,
                default=1.0,
                required=False
            ),
            Option(
                name='pitch',
                description='Pitch of the track.',
                type=float,
                default=1.0,
                required=False
            ),
            Option(
                name='rate',
                description='Rate of the track.',
                type=float,
                default=1.0,
                required=False
            ),
        ]
    )
    async def timescale(self, ctx, preset: str = 'custom', speed: float = 1.0, pitch: float = 1.0, rate: float = 1.0) -> None:

        # Ensure parameters are floats
        speed = float(speed)
        pitch = float(pitch)
        rate = float(rate)

        player: Player = ctx.voice_client

        if preset.lower() == 'nightcore':
            # Apply the nightcore preset using the class method
            pomice_filter = pomice.filters.Timescale.nightcore()
            await ctx.respond('Nightcore filter applied', delete_after=5)
        else:
            # Apply custom timescale adjustments
            pomice_filter = pomice.filters.Timescale(tag='custom', speed=float(speed), pitch=float(pitch), rate=float(rate))
            await ctx.respond(f'Timescale filter applied with speed: {speed}, pitch: {pitch}, rate: {rate}', delete_after=5)

        # Apply the filter to the player
        await player.add_filter(pomice_filter, fast_apply=True)

    @filter.command(
        name='tremolo',
        description='Rapidly changes the volume of the track.',
        options=[
            Option(name='frequency', description='Frequency of the tremolo effect.', type=float, default=2.0),
            Option(name='depth', description='Depth of the tremolo effect.', type=float, default=0.5),
        ]
    )    
    async def tremolo(self, ctx, frequency: float, depth: float) -> None:
        pomice_filter = pomice.filters.Tremolo(tag='tremolo', frequency=float(frequency), depth=float(depth))
        player: Player = ctx.voice_client
        await player.add_filter(pomice_filter, fast_apply=True)
        await ctx.respond('Tremolo filter applied', delete_after=5)

    @filter.command(
        name='vibrato',
        description='Rapidly changes the pitch of the track.',
        options=[
            Option(name='frequency', description='Frequency of the vibrato effect.', type=float, default=2.0),
            Option(name='depth', description='Depth of the vibrato effect.', type=float, default=0.5),
        ]
    )
    async def vibrato(self, ctx, frequency: float, depth: float) -> None:
        pomice_filter = pomice.filters.Vibrato(tag='vibrato', frequency=float(frequency), depth=float(depth))
        player: Player = ctx.voice_client
        await player.add_filter(pomice_filter, fast_apply=True)
        await ctx.respond('Vibrato filter applied', delete_after=5)

def setup(bot):
    bot.add_cog(Filter(bot))
