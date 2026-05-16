# 檔名：rpg_system.py

class Achievement:
    def __init__(self, name, desc, condition):
        self.name = name
        self.desc = desc
        self.condition = condition
        self.unlocked = False

class Skill:
    def __init__(self, name):
        self.name = name
        self.level = 0
        self.point = 0
        self.sub_skill = []

    def gain_skill_point(self, amount):
        self.point += amount
        self.level_up()

    def level_up(self):
        while self.point >= 60:
            self.point -= 60
            self.level += 1
            print(f" 恭喜【{self.name}】升到 Lv.{self.level}！")

    def add_subskill(self, subskill):
        self.sub_skill.append(subskill)

class Player:
    def __init__(self, name):
        self.name = name
        self.exp = 0
        self.level = 0
        self.skills = []
        self.achievements = []
        self.init_achievements()

    def gain_exp(self, task_minutes):
        if task_minutes <= 25:
            amount = 10
        elif task_minutes < 50:
            amount = 20
        else:
            amount = 30

        print(f"\n>>> {self.name} 獲得了 {amount} 點經驗值")
        self.exp += amount
        self.level_up()
        self.check_achievements()

    def level_up(self):
        while self.exp >= 100 * (self.level + 1):
            required = 100 * (self.level + 1)
            self.exp -= required
            self.level += 1
            print(f"🎉 恭喜 {self.name} 升到 {self.level} 級！")

    def init_achievements(self):
        self.achievements = [
            Achievement("初學者", "達到等級 1", lambda p: p.level >= 1),
            Achievement("穩定成長者", "達到等級 5", lambda p: p.level >= 5),
            Achievement("努力不懈", "達到等級 10", lambda p: p.level >= 10),
            Achievement("技能專家", "任一技能達到 Lv10", lambda p: any(skill.level >= 10 for skill in p.skills)),
            Achievement("全能型玩家", "所有技能都達到 Lv5", lambda p: all(skill.level >= 5 for skill in p.skills)),
        ]

    def check_achievements(self):
        for a in self.achievements:
            if not a.unlocked and a.condition(self):
                a.unlocked = True
                print(f" 🏆 解鎖成就：【{a.name}】- {a.desc}")

def initial_skill(player_object):
    player_object.skills.append(Skill("學習能力"))
    player_object.skills.append(Skill("工作能力"))
    player_object.skills.append(Skill("生活技能"))
    player_object.skills.append(Skill("運動能力"))