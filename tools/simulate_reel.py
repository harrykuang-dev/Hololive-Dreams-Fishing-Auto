"""Offline control stress model, NOT a game win-rate measurement."""
import json
import math
from pathlib import Path
import subprocess
import sys
import types
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bot_control import ReelControl, Tracking
from bot_input import ReelActuator


def simulate(factory, fps, latency, bar, independent):
    # Toy inertial slider: these dynamics are deliberately explicit and are
    # not claimed to have been measured from hololive Dreams.
    clock = [0.]
    class Input:
        pressed = False
        def press(self, _point): self.pressed = True
        def release(self): self.pressed = False
    mouse = Input()
    actuator = ReelActuator(mouse,clock=lambda:clock[0])
    control = factory(.20)
    player,velocity = 350.,0.
    dt = .005
    history = []
    errors = []
    next_frame = 0.
    for i in range(round(20/dt)):
        now = clock[0] = i*dt
        fish = 350+90*math.sin(now*2.5)
        fish_v = 225*math.cos(now*2.5)
        history.append((player,velocity,fish,fish_v))
        if now >= next_frame:
            sample = history[max(0,i-round(latency/dt))]
            p,v,f,fv = sample
            tracking = Tracking(p,f,bar,v,fv)
            if independent:
                _,mode,_ = control.decide(tracking,700,latency=latency)
                actuator.submit((0,0),mode,control.duty)
            else:
                mouse.pressed = control.decide(tracking,700)[0]
            # Repeatable processing jitter to stress variable sample timing.
            next_frame = now+(1/fps)*(1+.25*math.sin(i*.7))
        if independent:
            actuator.tick()
        target_velocity = -330 if mouse.pressed else 330
        velocity += (target_velocity-velocity)*(1-math.exp(-dt/.065))
        player = max(60,min(640,player+velocity*dt))
        if now > 2:
            errors.append(abs(player-fish))
    actuator.close()
    return dict(mean_error=round(sum(errors)/len(errors),2),
                inside_percent=round(100*sum(e<bar/2 for e in errors)/len(errors),1))


def main():
    module = types.ModuleType('control_baseline')
    sys.modules[module.__name__] = module
    source = subprocess.run(['git','show','bcb166f:bot_control.py'],capture_output=True,
                            text=True,encoding='utf-8',check=True).stdout
    exec(compile(source,'control_baseline.py','exec'),module.__dict__)
    results = []
    for fps in (10,15,20,40):
        for latency in (0,.04,.08):
            for bar in (24,50):
                results.append(dict(fps=fps,latency_ms=latency*1000,bar=bar,
                    baseline=simulate(module.ReelControl,fps,latency,bar,False),
                    revised=simulate(ReelControl,fps,latency,bar,True)))
    print(json.dumps({'mode':'toy_simulation_not_game_win_rate','cases':results},indent=2))


if __name__ == '__main__': main()
