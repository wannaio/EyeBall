# EyeBall - A Game For Lazy Days :video_game:
:eyes: Lay back and watch the ball roll where you want it to go. \
:robot: Compete with an RL agent.

https://github.com/user-attachments/assets/c6453af5-356f-43d6-bf2e-d8a2a4e8e33b

*Avoid obstacles by jumping or swaping lanes*

## Setup

### Prerequisite for eye tracking
If you are on Windows you need [Microsoft Visual C++ Redistributable 2015-2022](https://aka.ms/vs/17/release/vc_redist.x64.exe) to run mediapipe, else you get DLL load errors.\
Check your architecture with:
```bash
python -c "import platform; print(platform.architecture())"
```

### Get started
1. create environment with `conda env create -f environment.yaml`
2. activate it with `conda activate eye`
3. optional: train the RL agent with `python src/rl/train_agent.py` (else it will use the pretrianed agent in `src/rl/models/`)
4. run the game with `python src/app.py`.

## How to play
Avoid obstacles by swaping lanes or jumping over them.

- restart with `r` if you hit an obstacle
- restart with `shift + r` if you want to restart the game during gameplay
- toggle eye tracker ON/OFF with `e`

### Control
1. Keyboard controls:
- Left: `a`
- Right: `d`
- Jump: `space`

2. Eye tracking controls

https://github.com/user-attachments/assets/3aa9edcc-a89a-4111-9262-340c57370f82

- Jump: `space`


## Planned Todos (in no particular order)
<details>
<summary>Click to expand</summary>

- [x] Implement eye tracking to control game
- [x] Add RL agent --> train to play the game
- [x] Add ability compete with the RL agent (in the same game)

</details>
