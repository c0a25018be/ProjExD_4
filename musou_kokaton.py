import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img, (+1, -1): pg.transform.rotozoom(img, 45, 0.9),
            (0, -1): pg.transform.rotozoom(img, 90, 0.9), (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),
            (-1, 0): img0, (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),
            (0, +1): pg.transform.rotozoom(img, -90, 0.9), (+1, +1): pg.transform.rotozoom(img, -45, 0.9),
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        super().__init__()
        rad = random.randint(10, 50)
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"  # 追加：爆弾の状態（通常はactive）

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    def __init__(self, bird: Bird):
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    def __init__(self, obj: "Bomb|Enemy", life: int):
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)
        self.state = "down"
        self.interval = random.randint(50, 300)

    def update(self):
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Score:
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)
        
        
class Shield(pg.sprite.Sprite):
    """
    こうかとんを守る防壁に関するクラス
    """
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        self.life = life
        
        width = 20
        height = bird.rect.height*2
        self.image = pg.Surface((width,height))        
        pg.draw.rect(self.image, (0, 0 ,255), (0, 0, width, height))        
        vx,vy= bird.dire        
        angle = math.degrees(math.atan2(-vy, vx))        
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        self.image.set_colorkey((0, 0, 0))
        
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx + bird.rect.width * vx
        self.rect.centery = bird.rect.centery + bird.rect.height * vy
        
    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()
    

# --- 追加機能1：Lifeクラス ---
class Life:
    def __init__(self, num: int):
        self.num = num
        # 実装例：40x40の空のSurface
        self.image = pg.Surface((40, 40))
        self.image.set_colorkey((0, 0, 0))
        
        # 実装例：ハートの描き方
        points = [
            ((16*math.sin(t/100)**3 + 20),
             -(13*math.cos(t/100)-5*math.cos(2*t/100)-2*math.cos(3*t/100)-math.cos(4*t/100)) + 20)
            for t in range(0, 628)
        ]
        pg.draw.polygon(self.image, (255, 0, 0), points)

    def update(self, screen: pg.Surface):
        # 実装例：ハートが描画されたsurfaceをnum個blitする
        # 位置：最右ハートの重心が下から50, 右から50
        # Surfaceが40x40なので、左上座標は (WIDTH-50-20, HEIGHT-50-20)
        for i in range(self.num):
            screen.blit(self.image, (WIDTH - 70 - (i * 40), HEIGHT - 70))


class EMP:
    """
    追加機能3：電磁パルス（EMP）に関するクラス
    """
    def __init__(self, enemies: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        """
        発動時に存在する敵機と爆弾を無効化する
        """
        # 敵機の無効化
        for emy in enemies:
            emy.interval = float("inf")  # 爆弾投下不能にする
            # ラプラシアンフィルタを掛ける
            emy.image = pg.transform.laplacian(emy.image)
            emy.image.set_colorkey((0, 0, 0))

        # 爆弾の無効化
        for bomb in bombs:
            bomb.speed /= 2          # 動きを遅くする
            bomb.state = "inactive"  # ぶつかっても爆発しない状態にする

        # エフェクト：画面全体に透明度のある黄色の矩形を表示
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (255, 255, 0), (0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(100)  # 透明度
        self.rect = self.image.get_rect()
        self.life = 3  # 0.05秒程度（60FPS想定で約3フレーム）

    def update(self, screen: pg.Surface):
        """
        エフェクトを描画し、lifeを減らす
        """
        if self.life > 0:
            screen.blit(self.image, self.rect)
            self.life -= 1


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    # 実装例：main関数の初期化部分でLifeインスタンスを生成
    life = Life(3)

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()
    emp_effect = None  # EMPエフェクト保持用

    tmr = 0
    clock = pg.time.Clock()
    
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
        
            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                if score.value > 50 and len(shields) == 0:
                    shields.add(Shield(bird, 400))
                    score.value -= 50             
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                # 追加機能3：EMP発動条件
                if event.key == pg.K_e and score.value >= 20:
                    score.value -= 20
                    emp_effect = EMP(emys, bombs, screen)

        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                bombs.add(Bomb(emy, bird))

        # ビームと敵の衝突
        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.value += 10
            bird.change_img(6, screen)

        # ビームと爆弾の衝突
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1

        # こうかとんと爆弾の衝突
        if pg.sprite.spritecollide(bird, bombs, True):
            life.num -= 1
            bird.change_img(8, screen)
            
            if life.num == 0:
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        for bomb in pg.sprite.groupcollide(bombs, shields, True, False).keys():
            exps.add(Explosion(bomb, 50)) 
            if bomb.state == "active":  # EMPで無効化されていない場合のみ終了
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            else:
                # EMP無効化中の爆弾に当たった場合は、爆発せずに消滅（実装例より）
                continue

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        
        # EMPエフェクトの更新と描画
        if emp_effect:
            emp_effect.update(screen)

        score.update(screen)
        
        # ライフの表示更新
        life.update(screen)
        
        shields.update()
        shields.draw(screen) 
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()