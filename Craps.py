import random
import pygame

UI_COMPONENT_MOUSEMOTION =            pygame.USEREVENT + 1
UI_COMPONENT_MOUSEBUTTONDOWN =        pygame.USEREVENT + 2
TABLE_MOUSEMOTION =                   pygame.USEREVENT + 3
TABLE_MOUSEBUTTONDOWN =               pygame.USEREVENT + 4
TABLE_BET_MOUSEMOTION =               pygame.USEREVENT + 5
TABLE_BET_MOUSEBUTTONDOWN =           pygame.USEREVENT + 6
BET_MANAGER_BET_HOVER =               pygame.USEREVENT + 7
BET_MANAGER_BET_PLACED =              pygame.USEREVENT + 8
CHIP_TRAY_MOUSEMOTION =               pygame.USEREVENT + 9
CHIP_TRAY_MOUSEBUTTONDOWN =           pygame.USEREVENT + 10
CHIP_TRAY_MANAGER_CHIP_HOVER =        pygame.USEREVENT + 11
CHIP_TRAY_MANAGER_CHIP_SELECTED =     pygame.USEREVENT + 12
DICE_SET_MOUSEMOTION =                pygame.USEREVENT + 13
DICE_SET_MOUSEBUTTONDOWN =            pygame.USEREVENT + 14
DICE_MANAGER_DICE_HOVER =             pygame.USEREVENT + 15
DICE_MANAGER_DICE_ROLLED =            pygame.USEREVENT + 16
PUCK_MANAGER_POINT_SET =              pygame.USEREVENT + 17
PUCK_MANAGER_POINT_WIN =              pygame.USEREVENT + 18
PUCK_MANAGER_POINT_LOSE =             pygame.USEREVENT + 19
BET_MANAGER_BET_WIN =                 pygame.USEREVENT + 20
BET_MANAGER_BET_LOSE =                pygame.USEREVENT + 21
BET_MANAGER_BET_PUSH =                pygame.USEREVENT + 22
BET_MANAGER_OVERALL_WIN =             pygame.USEREVENT + 23
BET_MANAGER_OVERALL_LOSE =            pygame.USEREVENT + 24
BET_MANAGER_OVERALL_PUSH =            pygame.USEREVENT + 25

WIN = "WIN"
LOSE = "LOSE"

def run():
    craps = Craps("Craps", (1280, 1280//2))
    craps.run()

class Craps:
    def __init__(self, caption: str, size: "tuple[int, int]") -> None:
        pygame.init()
        pygame.display.set_caption(caption)

        self.surface = pygame.display.set_mode(size, pygame.DOUBLEBUF, 32)
        self.clock = pygame.time.Clock()
        self.running = True
        self.fps = 60
        self.font = pygame.font.SysFont(None, 24)
        self.ms = 0
        self.size = size
        self.screen_rect = pygame.rect.Rect((0, 0), size)

        self.ui_component = UIComponent(None, self.screen_rect)
        self.table_manager = TableManager(self.ui_component, self.screen_rect, "craps_table_correct.png", "craps_table_regions.png")
        self.bet_manager = BetManager(self.ui_component, self.screen_rect)
        self.chip_tray_manager = ChipTrayManager(self.ui_component, self.screen_rect)
        self.puck_manager = PuckManager(self.ui_component, self.screen_rect)
        self.dice_manager = DiceManager(self.ui_component, self.screen_rect)
        self.money_manager = MoneyManager(self.ui_component, self.screen_rect)
        self.tooltip_manager = ToolTipManager(self.ui_component, self.screen_rect)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(self.fps)
            self.ms += dt
            self.surface.fill((255, 255, 255))

            self.event_loop()

            self.ui_component.update(dt)
            self.ui_component.draw(self.surface, self.screen_rect)

            pygame.display.flip()

            component_count = self.ui_component.get_component_count()
            if component_count > 1000:
                print("WARNING: Component Count Exceeds 1000: %d" % component_count)

    def event_loop(self) -> None:
        event_loop_running = True
        while event_loop_running:
            event_loop_running = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                events_to_post: "list[pygame.event.Event]" = []
                self.ui_component.handle_event(event, events_to_post)

                for event_to_post in events_to_post:
                    pygame.event.post(event_to_post)
                    event_loop_running = True

class UIComponent:
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect) -> None:
        self.ms = 0
        self.rect = rect
        self.parent: UIComponent = parent
        self.child_components: "list[UIComponent]" = []
        self.alive = True
        self.draw_bounds = False

        if parent:
            parent.child_components.append(self)

    def get_component_count(self) -> int:
        count = 1

        for child in self.child_components:
            count += child.get_component_count()

        return count

    def destroy(self) -> None:
        self.alive = False

        for child in self.child_components:
            child.destroy()

    def update(self, dt: int) -> None:
        self.ms += dt

        all_alive = True
        for child in self.child_components:
            child.update(dt)
            if not child.alive:
                all_alive = False

        if not all_alive:
            self.child_components = [child for child in self.child_components if child.alive]

    def draw(self, surface: pygame.Surface, bounds: pygame.rect.Rect) -> None:
        if self.draw_bounds:
            pygame.draw.rect(surface, (0, 0, 0), bounds, 1)

        for child in self.child_components:
            child_surface = pygame.Surface(child.rect.size, pygame.SRCALPHA)
            child_rect = child.rect.copy()
            child_rect.topleft = (0, 0)
            child.draw(child_surface, child_rect)
            surface.blit(child_surface, child.rect)

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                relative_mouse = (mouse_pos[0] - self.rect.x, mouse_pos[1] - self.rect.y)
                
                if event.type == pygame.MOUSEMOTION:
                    event_type = UI_COMPONENT_MOUSEMOTION
                else:
                    event_type = UI_COMPONENT_MOUSEBUTTONDOWN

                event_to_post = pygame.event.Event(event_type, {
                    "pos": relative_mouse,
                    "screen_pos": mouse_pos,
                    "component": self
                })

                events_to_post.append(event_to_post)
        
        for child in self.child_components:
            child.handle_event(event, events_to_post)

class Text(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", text: str, color: "tuple[int, int, int]", text_size: int) -> None:
        super().__init__(parent, None)

        self.text = text
        font = pygame.font.Font(None, text_size)

        self.text_render = font.render(text, True, color)
        self.rect = self.text_render.get_rect()
        self.rect.topleft = pos

    def draw(self, surface: pygame.Surface, bounds: pygame.rect.Rect) -> None:
        surface.blit(self.text_render, bounds)

        super().draw(surface, bounds)

class MultiLineText(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", text: "list[str]", text_size: int) -> None:
        super().__init__(parent, None)

        self.text = text
        
        line_spacing = 5

        left = 0
        top = 0
        width = 0
        height = 0

        for line in self.text:
            child = Text(self, (left, top), line, (0, 0, 0), text_size)

            width = max(width, child.rect.width)
            height += child.rect.height + line_spacing
            top += child.rect.height + line_spacing

        height -= line_spacing
        self.rect = pygame.rect.Rect(pos, (width, height))

class ToolTip(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", text: "list[str]") -> None:
        super().__init__(parent, None)

        self.text = text

        padding = 5
        text_size = 24
        self.multiline = MultiLineText(self, (padding, padding), text, text_size)

        self.rect = pygame.rect.Rect(pos, (self.multiline.rect.width + padding * 2, self.multiline.rect.height + padding * 2))

    def draw(self, surface: pygame.Surface, bounds: pygame.rect.Rect) -> None:
        pygame.draw.rect(surface, (255, 255, 255, 192), bounds, 0, 5)
        pygame.draw.rect(surface, (0, 0, 0), bounds, 1, 5)

        super().draw(surface, bounds)

class TableManager(UIComponent):
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect, table_img_path: str, regions_img_path: str) -> None:
        super().__init__(parent, rect)

        self.table_img = pygame.image.load(table_img_path)
        self.table_img = pygame.transform.scale(self.table_img, rect.size)

        self.regions_img = pygame.image.load(regions_img_path)
        self.regions_img = pygame.transform.scale(self.regions_img, rect.size)

        self.define_regions()

    def define_regions(self) -> None:
        self.regions_mapping: "dict[tuple[int, int, int], str]" = {
            (0, 0, 0): "",
            (50, 50, 50): "Pass Line",
            (55, 55, 55): "Don't Pass",
            (60, 60, 60): "Big 6",
            (65, 65, 65): "Big 8",
            (70, 70, 70): "Field",
            (75, 75, 75): "Come",
            (80, 80, 80): "Don't Come",
            (85, 85, 85): "Place 4",
            (90, 90, 90): "Place 5",
            (95, 95, 95): "Place 6",
            (100, 100, 100): "Place 8",
            (105, 105, 105): "Place 9",
            (110, 110, 110): "Place 10",
            (115, 115, 115): "Any 7",
            (120, 120, 120): "Hard 6",
            (125, 125, 125): "Hard 10",
            (130, 130, 130): "Hard 8",
            (135, 135, 135): "Hard 4",
            (140, 140, 140): "Three",
            (145, 145, 145): "Two",
            (150, 150, 150): "Twelve",
            (155, 155, 155): "Eleven",
            (160, 160, 160): "Any Craps"}

    def draw(self, surface: pygame.Surface, bounds: pygame.rect.Rect) -> None:
        surface.blit(self.table_img, bounds)

        super().draw(surface, bounds)

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if (event.type == UI_COMPONENT_MOUSEMOTION or event.type == UI_COMPONENT_MOUSEBUTTONDOWN) and event.component == self:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            color = self.regions_img.get_at(pos)[:3]
            bet = self.regions_mapping[color]

            if event.type == UI_COMPONENT_MOUSEMOTION:
                event_type = TABLE_MOUSEMOTION
            else:
                event_type = TABLE_MOUSEBUTTONDOWN
                print("Click", bet, pos, (pos[0] / self.rect.width, pos[1] / self.rect.height))
                
            event_to_post = pygame.event.Event(event_type, {
                "pos": pos,
                "screen_pos": screen_pos,
                "color": color
            })

            events_to_post.append(event_to_post)

            if bet:
                if event.type == UI_COMPONENT_MOUSEMOTION:
                    event_type = TABLE_BET_MOUSEMOTION
                else:
                    event_type = TABLE_BET_MOUSEBUTTONDOWN
                    
                event_to_post = pygame.event.Event(event_type, {
                    "pos": pos,
                    "screen_pos": screen_pos,
                    "color": color,
                    "bet": bet
                })

                events_to_post.append(event_to_post)

class ToolTipManager(UIComponent):
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect) -> None:
        super().__init__(parent, rect)

        self.hover_tooltip: ToolTip = None
        self.clear_tooltip = False

    def update(self, dt: int) -> None:
        super().update(dt)

        if self.clear_tooltip and self.hover_tooltip is not None:
            self.hover_tooltip.destroy()
            self.clear_tooltip = False

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if event.type == TABLE_MOUSEMOTION or event.type == TABLE_MOUSEBUTTONDOWN:
            self.clear_tooltip = True

        elif event.type == BET_MANAGER_BET_HOVER or event.type == BET_MANAGER_BET_PLACED:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            color: "tuple[int, int, int]" = event.color
            bet: str = event.bet
            current_bet: int = event.current_bet
            amount_added: int = event.amount_added

            self.create_tooltip([bet, "$%d" % current_bet], screen_pos)

        elif event.type == CHIP_TRAY_MANAGER_CHIP_HOVER or event.type == CHIP_TRAY_MANAGER_CHIP_SELECTED:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            selected_chip: int = event.selected_chip
            current_chip: int = event.current_chip

            self.create_tooltip(["Select a Chip", "Current: $%d" % current_chip, "$%d" % selected_chip], screen_pos)

        elif event.type == DICE_MANAGER_DICE_HOVER or event.type == DICE_MANAGER_DICE_ROLLED:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            dice_total: int = event.dice_total
            dice_values: "list[int]" = event.dice_values

            self.create_tooltip(["Roll the Dice", "Current: %d" % dice_total], screen_pos)

    def create_tooltip(self, lines: "list[str]", pos: "tuple[int, int]") -> None:
            self.clear_tooltip = False

            if self.hover_tooltip is not None:
                self.hover_tooltip.destroy()

            self.hover_tooltip = ToolTip(self, pos, lines)

            if pos[0] / self.rect.width > 0.5:
                self.hover_tooltip.rect.left -= self.hover_tooltip.rect.width + 10
            else:
                self.hover_tooltip.rect.left += 15

            if pos[1] / self.rect.height > 0.5:
                self.hover_tooltip.rect.top -= self.hover_tooltip.rect.height + 5
            else:
                self.hover_tooltip.rect.top += 10

class Chip(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", text: str, size: int) -> None:
        super().__init__(parent, None)

        chip_size = size
        text_color_mapping: "dict[str, tuple[int, int, int]]" = {
            "1": (244, 224, 137),
            "5": (244, 224, 137),
            "25": (244, 224, 137),
            "100": (244, 224, 137),
            "ON": (0, 0, 0),
            "OFF": (255, 255, 255)
        }
        color_mapping: "dict[str, tuple[int, int, int]]" = {
            "1": (255, 255, 255),
            "5": (241, 148, 141),
            "25": (122, 195, 150),
            "100": (131, 131, 131),
            "ON": (255, 255, 255),
            "OFF": (0, 0, 0)
        }
        border_color_mapping: "dict[str, tuple[int, int, int]]" = {
            "1": (0, 0, 0),
            "5": (0, 0, 0),
            "25": (0, 0, 0),
            "100": (0, 0, 0),
            "ON": (0, 0, 0),
            "OFF": (255, 255, 255)
        }

        self.chip_color = color_mapping[text]
        self.text_color = text_color_mapping[text]
        self.border_color = border_color_mapping[text]
        self.text = text
        self.text = Text(self, (0, 0), text, self.text_color, int(0.65 * size))

        self.rect = pygame.rect.Rect(0, 0, chip_size, chip_size)
        self.text.rect.center = self.rect.center
        self.rect.center = pos

    def draw(self, surface: pygame.Surface, bounds: pygame.rect.Rect) -> None:
        pygame.draw.circle(surface, self.chip_color, bounds.center, bounds.width // 2)
        pygame.draw.circle(surface, self.border_color, bounds.center, bounds.width // 2, 1)

        super().draw(surface, bounds)

class ChipStack(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", amount: int, chip_size: int, offset: int) -> None:
        super().__init__(parent, None)

        chip_categories = [100, 25, 5, 1]
        chip_components = self.get_number_components(amount, chip_categories)

        width = chip_size
        height = chip_size + offset * (sum(chip_components) - 1)
        self.rect = pygame.rect.Rect((pos[0] - width // 2, pos[1] - (height - chip_size // 2)), (width, height))

        current_offset = height - chip_size // 2

        for category, component in zip(chip_categories, chip_components):
            for index in range(component):
                chip = Chip(self, (width // 2, current_offset), "%d" % category, chip_size)
                current_offset -= offset

    def get_number_components(self, number: int, categories: "list[int]") -> "list[int]":
        components: "list[int]" = []

        for category in categories:
            result = number // category
            number = number % category
            components.append(result)

        return components

class BetManager(UIComponent):
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect) -> None:
        super().__init__(parent, rect)

        self.bets: "dict[str, int]" = {}
        self.stacks: "dict[str, ChipStack]" = {}

        self.selected_amount = 1
        self.current_point = 0

        self.define_bet_coordinates()

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if event.type == TABLE_BET_MOUSEMOTION or event.type == TABLE_BET_MOUSEBUTTONDOWN:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            color: "tuple[int, int, int]" = event.color
            bet: str = event.bet

            amount_added = 0
            if event.type == TABLE_BET_MOUSEMOTION:
                event_type = BET_MANAGER_BET_HOVER
            else:
                self.add_bet(bet, self.selected_amount)
                amount_added = self.selected_amount
                event_type = BET_MANAGER_BET_PLACED
                
            current_bet = self.get_bet(bet)
            event_to_post = pygame.event.Event(event_type, {
                "pos": pos,
                "screen_pos": screen_pos,
                "color": color,
                "bet": bet,
                "current_bet": current_bet,
                "amount_added": amount_added
            })

            events_to_post.append(event_to_post)

        elif event.type == CHIP_TRAY_MANAGER_CHIP_SELECTED:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            selected_chip: int = event.selected_chip
            current_chip: int = event.current_chip

            self.selected_amount = selected_chip

        elif event.type == DICE_MANAGER_DICE_ROLLED:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            dice_total: int = event.dice_total
            dice_values: "list[int]" = event.dice_values

            self.dice_rolled(dice_total, dice_values, events_to_post)

        elif event.type == PUCK_MANAGER_POINT_SET or event.type == PUCK_MANAGER_POINT_WIN or event.type == PUCK_MANAGER_POINT_LOSE:
            dice_total: int = event.dice_total
            dice_values: "list[int]" = event.dice_values
            previous_point: int = event.previous_point
            current_point: int = event.current_point

            self.current_point = current_point

    def define_bet_coordinates(self) -> None:
        self.coordinate_mapping: "dict[str, tuple[int, int]]" = {
            "Pass Line": (0.46, 0.7725),
            "Don't Pass": (0.4925, 0.68),
            "Big 6": (0.13875, 0.545),
            "Big 8": (0.1675, 0.5975),
            "Field": (0.4675, 0.5825),
            "Come": (0.4675, 0.3925),
            "Don't Come": (0.165, 0.2675),
            "Place 4": (0.2675, 0.29),
            "Place 5": (0.34625, 0.29),
            "Place 6": (0.42375, 0.29),
            "Place 8": (0.5025, 0.29),
            "Place 9": (0.58125, 0.29),
            "Place 10": (0.65875, 0.29),
            "Any 7": (0.7375, 0.41),
            "Hard 6": (0.80375, 0.4925),
            "Hard 10": (0.85, 0.4925),
            "Hard 8": (0.80375, 0.6025),
            "Hard 4": (0.85, 0.6025),
            "Three": (0.74, 0.7375),
            "Two": (0.835, 0.735),
            "Twelve": (0.9275, 0.735),
            "Eleven": (0.80375, 0.8225),
            "Any Craps": (0.7375, 0.9075)}

    def determine_bet_outcome(self, bet: str, dice_total: int, dice_values: "list[int]") -> "tuple[str, int, int]":
        if bet == "Pass Line":
            if self.current_point == 0:
                if dice_total in (7, 11):
                    return WIN, 1, 1
                elif dice_total in (2, 3, 12):
                    return LOSE, 0, 1
            else:
                if dice_total == self.current_point:
                    return WIN, 1, 1
                elif dice_total == 7:
                    return LOSE, 0, 1

        elif bet == "Don't Pass":
            if self.current_point == 0:
                if dice_total in (7, 11):
                    return LOSE, 0, 1
                elif dice_total in (2, 3):
                    return WIN, 1, 1
            else:
                if dice_total == self.current_point:
                    return LOSE, 0, 1
                elif dice_total == 7:
                    return WIN, 1, 1

        elif bet == "Big 6":
            if dice_total == 6:
                return WIN, 1, 1
            elif dice_total == 7:
                return LOSE, 0, 1

        elif bet == "Big 8":
            if dice_total == 8:
                return WIN, 1, 1
            elif dice_total == 7:
                return LOSE, 0, 1

        elif bet == "Field":
            if dice_total in (2, 12):
                return WIN, 2, 1
            elif dice_total in (3, 4, 9, 10, 11):
                return WIN, 1, 1
            else:
                return LOSE, 0, 1

        elif bet == "Come":
            if dice_total in (7, 11):
                return WIN, 1, 1
            elif dice_total in (2, 3, 12):
                return LOSE, 0, 1

        elif bet == "Don't Come":
            if dice_total in (7, 11):
                return LOSE, 0, 1
            elif dice_total in (2, 3):
                return WIN, 1, 1

        elif bet == "Place 4":
            if dice_total == 4:
                return WIN, 9, 5
            elif dice_total == 7 and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Place 5":
            if dice_total == 5:
                return WIN, 7, 5
            elif dice_total == 7 and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Place 6":
            if dice_total == 6:
                return WIN, 7, 6
            elif dice_total == 7 and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Place 8":
            if dice_total == 8:
                return WIN, 7, 6
            elif dice_total == 7 and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Place 9":
            if dice_total == 9:
                return WIN, 7, 5
            elif dice_total == 7 and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Place 10":
            if dice_total == 10:
                return WIN, 9, 5
            elif dice_total == 7 and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Any 7":
            if dice_total == 7:
                return WIN, 4, 1
            else:
                return LOSE, 0, 1

        elif bet == "Hard 6":
            if dice_values == [3, 3]:
                return WIN, 9, 1
            elif dice_total in (6, 7) and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Hard 10":
            if dice_values == [5, 5]:
                return WIN, 7, 1
            elif dice_total in (10, 7) and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Hard 8":
            if dice_values == [4, 4]:
                return WIN, 9, 1
            elif dice_total in (8, 7) and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Hard 4":
            if dice_values == [2, 2]:
                return WIN, 7, 1
            elif dice_total in (4, 7) and self.current_point != 0:
                return LOSE, 0, 1

        elif bet == "Three":
            if dice_total == 3:
                return WIN, 15, 1
            else:
                return LOSE, 0, 1

        elif bet == "Two":
            if dice_total == 2:
                return WIN, 30, 1
            else:
                return LOSE, 0, 1

        elif bet == "Twelve":
            if dice_total == 12:
                return WIN, 30, 1
            else:
                return LOSE

        elif bet == "Eleven":
            if dice_total == 11:
                return WIN, 15, 1
            else:
                return LOSE, 0, 1

        elif bet == "Any Craps":
            if dice_total in (2, 3, 12):
                return WIN, 7, 1
            else:
                return LOSE, 0, 1
            
        else:
            raise RuntimeError("Invalid bet: %s" % bet)

        return "", 0, 1

    def dice_rolled(self, dice_total: int, dice_values: "list[int]", events_to_post: "list[pygame.event.Event]") -> None:
        total_win = 0
        current_bets = list(self.bets.items())
        for bet, amount in current_bets:
            outcome, win, to = self.determine_bet_outcome(bet, dice_total, dice_values)

            win_amount = int(amount * 100 * win / to) / 100
            print("Bet %s $%d wins %s" % (bet, amount, win_amount))

            if outcome == WIN:
                total_win += win_amount
                event_type = BET_MANAGER_BET_WIN

            elif outcome == LOSE:
                self.clear_bet(bet)
                total_win -= amount
                event_type = BET_MANAGER_BET_LOSE

            else:
                event_type = BET_MANAGER_BET_PUSH

            event_to_post = pygame.event.Event(event_type, {
                "dice_total": dice_total,
                "dice_values": dice_values,
                "bet": bet,
                "bet_amount": amount,
                "amount": win_amount
            })

            events_to_post.append(event_to_post)

        if total_win > 0:
            event_type = BET_MANAGER_OVERALL_WIN

        elif total_win < 0:
            event_type = BET_MANAGER_OVERALL_LOSE

        else:
            event_type = BET_MANAGER_OVERALL_PUSH

        event_to_post = pygame.event.Event(event_type, {
            "dice_total": dice_total,
            "dice_values": dice_values,
            "amount": abs(total_win)
        })

        events_to_post.append(event_to_post)

    def get_bet(self, bet: str) -> int:
        if bet not in self.bets:
            return 0

        return self.bets[bet]

    def add_bet(self, bet: str, amount: int) -> None:
        if bet not in self.bets:
            self.bets[bet] = 0
        else:
            self.stacks[bet].destroy()

        stack_pos = (int(self.coordinate_mapping[bet][0] * self.rect.width), int(self.coordinate_mapping[bet][1] * self.rect.height))
        chip_size = int(0.0234375 * self.rect.width)
        stack_offset = int(0.00234375 * self.rect.width)

        self.bets[bet] += amount
        self.stacks[bet] = ChipStack(self, stack_pos, self.bets[bet], chip_size, stack_offset)

    def clear_bet(self, bet: str) -> None:
        if bet not in self.bets:
            return

        self.stacks[bet].destroy()

        del self.bets[bet]
        del self.stacks[bet]

class ChipTray(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", chip_size: int) -> None:
        super().__init__(parent, None)

        self.chip_categories = [1, 5, 25, 100]

        padding = 10
        width = padding + (chip_size + padding) * len(self.chip_categories)
        height = chip_size + padding * 2
        self.rect = pygame.rect.Rect(pos, (width, height))

        for index, category in enumerate(self.chip_categories):
            chip_x = padding + chip_size // 2 + (chip_size + padding) * index
            chip_y = chip_size // 2 + padding
            chip = Chip(self, (chip_x, chip_y), "%d" % category, chip_size)

    def draw(self, surface: pygame.Surface, bounds: pygame.rect.Rect) -> None:
        pygame.draw.rect(surface, (255, 255, 255, 192), bounds, 0, 5)
        pygame.draw.rect(surface, (0, 0, 0), bounds, 1, 5)

        super().draw(surface, bounds)

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if (event.type == UI_COMPONENT_MOUSEMOTION or event.type == UI_COMPONENT_MOUSEBUTTONDOWN) and event.component == self:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos

            selected_chip = int(pos[0] / (self.rect.width / len(self.chip_categories)))

            if event.type == UI_COMPONENT_MOUSEMOTION:
                event_type = CHIP_TRAY_MOUSEMOTION
            else:
                event_type = CHIP_TRAY_MOUSEBUTTONDOWN
                
            event_to_post = pygame.event.Event(event_type, {
                "pos": pos,
                "screen_pos": screen_pos,
                "selected_chip": self.chip_categories[selected_chip]
            })

            events_to_post.append(event_to_post)

class ChipTrayManager(UIComponent):
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect) -> None:
        super().__init__(parent, rect)

        chip_size = int(0.0390625 * rect.width)
        tray_x = rect.x + 10
        tray_y = rect.bottom - 10
        self.chip_tray = ChipTray(self, (tray_x, tray_y), chip_size)
        self.chip_tray.rect.y -= self.chip_tray.rect.height

        self.selected_chip = self.chip_tray.chip_categories[0]

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if event.type == CHIP_TRAY_MOUSEMOTION or event.type == CHIP_TRAY_MOUSEBUTTONDOWN:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            selected_chip: int = event.selected_chip

            if event.type == CHIP_TRAY_MOUSEMOTION:
                event_type = CHIP_TRAY_MANAGER_CHIP_HOVER
            else:
                self.selected_chip = selected_chip
                event_type = CHIP_TRAY_MANAGER_CHIP_SELECTED
                
            event_to_post = pygame.event.Event(event_type, {
                "pos": pos,
                "screen_pos": screen_pos,
                "selected_chip": selected_chip,
                "current_chip": self.selected_chip
            })

            events_to_post.append(event_to_post)

class PuckManager(UIComponent):
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect) -> None:
        super().__init__(parent, rect)

        self.current_point = 0
        self.puck: Chip = None

        self.define_puck_coordinates()
        self.create_puck()

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if event.type == DICE_MANAGER_DICE_ROLLED:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            dice_total: int = event.dice_total
            dice_values: "list[int]" = event.dice_values

            event_type = 0
            previous_point = self.current_point

            if dice_total in (4, 5, 6, 8, 9, 10):
                if self.current_point == 0:
                    self.current_point = dice_total
                    self.create_puck()
                    event_type = PUCK_MANAGER_POINT_SET

                elif self.current_point == dice_total:
                    self.current_point = 0
                    self.create_puck()
                    event_type = PUCK_MANAGER_POINT_WIN

            elif dice_total in (7,) and self.current_point != 0:
                self.current_point = 0
                self.create_puck()
                event_type = PUCK_MANAGER_POINT_LOSE

            if event_type != 0:
                event_to_post = pygame.event.Event(event_type, {
                    "dice_total": dice_total,
                    "dice_values": dice_values,
                    "previous_point": previous_point,
                    "current_point": self.current_point
                })

                events_to_post.append(event_to_post)

    def create_puck(self) -> None:
        coords = (int(self.coordinate_mapping[self.current_point][0] * self.rect.width), int(self.coordinate_mapping[self.current_point][1] * self.rect.height))
        if self.current_point == 0:
            puck_text = "OFF"
        else:
            puck_text = "ON"

        if self.puck is not None:
            self.puck.destroy()

        self.puck = Chip(self, coords, puck_text, int(0.0625 * self.rect.width))

    def define_puck_coordinates(self) -> None:
        self.coordinate_mapping: "dict[int, tuple[int, int]]" = {
            0: (0.1671875, 0.1203125),
            4: (0.24453125, 0.125),
            5: (0.32265625, 0.125),
            6: (0.40078125, 0.125),
            8: (0.47734375, 0.125),
            9: (0.55703125, 0.125),
            10: (0.634375, 0.125)}

class Dice(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", number: int, size: int) -> None:
        super().__init__(parent, None)

        self.rect = pygame.rect.Rect(pos, (size, size))
        self.number = number

        self.pip_size_single = int(.16 * size)
        self.pip_size = int(.10 * size)

        self.pip_rect = self.rect.copy()
        self.pip_rect.width = int(.50 * self.pip_rect.width)
        self.pip_rect.height = int(.50 * self.pip_rect.height)

    def draw(self, surface: pygame.Surface, bounds: pygame.rect.Rect) -> None:
        pygame.draw.rect(surface, (238, 124, 121), bounds)
        pygame.draw.rect(surface, (0, 0, 0), bounds, 1)

        self.pip_rect.center = bounds.center
        if self.number == 1:
            self.draw_pip(surface, self.pip_rect.center, self.pip_size_single)
        
        elif self.number == 2:
            self.draw_pip(surface, self.pip_rect.topleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomright, self.pip_size)
        
        elif self.number == 3:
            self.draw_pip(surface, self.pip_rect.topleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.center, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomright, self.pip_size)
        
        elif self.number == 4:
            self.draw_pip(surface, self.pip_rect.topleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.topright, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomright, self.pip_size)
        
        elif self.number == 5:
            self.draw_pip(surface, self.pip_rect.center, self.pip_size)
            self.draw_pip(surface, self.pip_rect.topleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.topright, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomright, self.pip_size)
        
        elif self.number == 6:
            self.draw_pip(surface, self.pip_rect.topleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.midleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomleft, self.pip_size)
            self.draw_pip(surface, self.pip_rect.topright, self.pip_size)
            self.draw_pip(surface, self.pip_rect.midright, self.pip_size)
            self.draw_pip(surface, self.pip_rect.bottomright, self.pip_size)

        super().draw(surface, bounds)

    def draw_pip(self, surface: pygame.Surface, pos: "tuple[int, int]", size: int) -> None:
        pygame.draw.circle(surface, (255, 255, 255), pos, size)

class DiceSet(UIComponent):
    def __init__(self, parent: "UIComponent", pos: "tuple[int, int]", count: int, dice_size: int) -> None:
        super().__init__(parent, None)

        self.number_of_dice = 2
        self.dice_size = dice_size
        self.padding = 10
        self.dice: "list[Dice]" = []
        self.values: "list[int]" = []
        self.total = 0

        self.rect = pygame.rect.Rect(pos, (count * (dice_size + self.padding) - self.padding, dice_size))

        self.build_dice()

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if (event.type == UI_COMPONENT_MOUSEMOTION or event.type == UI_COMPONENT_MOUSEBUTTONDOWN) and event.component == self:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos

            if event.type == UI_COMPONENT_MOUSEMOTION:
                event_type = DICE_SET_MOUSEMOTION
            else:
                event_type = DICE_SET_MOUSEBUTTONDOWN
                
            event_to_post = pygame.event.Event(event_type, {
                "pos": pos,
                "screen_pos": screen_pos
            })

            events_to_post.append(event_to_post)

    def build_dice(self) -> None:
        for dice in self.dice:
            dice.destroy()
        
        self.dice = []
        self.values = []
        self.total = 0
        
        for index in range(self.number_of_dice):
            dice_roll = random.randint(1, 6)
            dice_x = (index * (self.dice_size + self.padding))
            dice_y = 0
            self.dice.append(Dice(self, (dice_x, dice_y), dice_roll, self.dice_size))
            self.values.append(dice_roll)
            self.total += dice_roll

class DiceManager(UIComponent):
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect) -> None:
        super().__init__(parent, rect)

        self.dice_size = int(0.0390625 * self.rect.width)
        padding = int(0.0078125 * rect.width)
        self.pos_x = int(0.203125 * rect.width + padding)
        self.pos_y = self.rect.bottom - self.dice_size - padding
        self.number_of_dice = 2
        self.dice_set: DiceSet = None

        self.create_dice()

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if event.type == DICE_SET_MOUSEMOTION or event.type == DICE_SET_MOUSEBUTTONDOWN:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos

            if event.type == DICE_SET_MOUSEMOTION:
                event_type = DICE_MANAGER_DICE_HOVER
            else:
                self.create_dice()
                event_type = DICE_MANAGER_DICE_ROLLED
                
            dice_total = self.dice_set.total
            dice_values = self.dice_set.values
            event_to_post = pygame.event.Event(event_type, {
                "pos": pos,
                "screen_pos": screen_pos,
                "dice_total": dice_total,
                "dice_values": dice_values
            })

            events_to_post.append(event_to_post)

    def create_dice(self) -> None:
        if self.dice_set is not None:
            self.dice_set.destroy()

        self.dice_set = DiceSet(self, (self.pos_x, self.pos_y), self.number_of_dice, self.dice_size)

class MoneyManager(UIComponent):
    def __init__(self, parent: "UIComponent", rect: pygame.rect.Rect) -> None:
        super().__init__(parent, rect)

        self.money = 10000
        self.betting = 0
        self.last_win = 0

        self.money_tooltip: ToolTip = None
        self.create_tooltip()

    def handle_event(self, event: pygame.event.Event, events_to_post: "list[pygame.event.Event]") -> None:
        super().handle_event(event, events_to_post)

        if event.type == BET_MANAGER_BET_PLACED:
            pos: "tuple[int, int]" = event.pos
            screen_pos: "tuple[int, int]" = event.screen_pos
            color: "tuple[int, int, int]" = event.color
            bet: str = event.bet
            current_bet: int = event.current_bet
            amount_added: int = event.amount_added

            self.money -= amount_added * 100
            self.betting += amount_added * 100

            self.create_tooltip()

        elif event.type == BET_MANAGER_BET_WIN or event.type == BET_MANAGER_BET_LOSE:
            dice_total: int = event.dice_total
            dice_values: "list[int]" = event.dice_values
            bet: str = event.bet
            bet_amount: int = event.bet_amount
            amount: int = event.amount

            if event.type == BET_MANAGER_BET_WIN:
                self.money += amount * 100
            else:
                self.betting -= bet_amount * 100

            self.create_tooltip()

        elif event.type == BET_MANAGER_OVERALL_WIN or event.type == BET_MANAGER_OVERALL_LOSE or event.type == BET_MANAGER_OVERALL_PUSH:
            dice_total: int = event.dice_total
            dice_values: "list[int]" = event.dice_values
            amount: int = event.amount

            if event.type == BET_MANAGER_OVERALL_WIN:
                self.last_win = amount * 100
            elif event.type == BET_MANAGER_OVERALL_LOSE:
                self.last_win = -1 * amount * 100
            else:
                self.last_win = 0

            self.create_tooltip()

    def create_tooltip(self) -> None:
        if self.money_tooltip is not None:
            self.money_tooltip.destroy()

        lines = [
            "Welcome to Craps!", 
            "Bank: $%.2f" % (self.money / 100), 
            "Betting: $%.2f" % (self.betting / 100), 
            "Last Win: $%.2f" % (self.last_win / 100)
        ]

        pos_x = int(0.684375 * self.rect.width)
        pos_y = int(0.0609375 * self.rect.height)
        width = int(0.2859375 * self.rect.width)
        height = int(0.290625 * self.rect.height)
        self.money_tooltip = ToolTip(self, (pos_x, pos_y), lines)
        self.money_tooltip.rect.width = width
        self.money_tooltip.rect.height = height

if __name__ == "__main__":
    run()