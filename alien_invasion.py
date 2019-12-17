import sys
import pygame
from time import sleep

from settings import Settings
from ship import Ship
from bullet import Bullet
from alien import Alien
from game_stats import GameStats
from button import Button
from scoreboard import Scoreboard

class AlienInvasion:
    """Overall class to manage game assets and behaviour."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        self.settings = Settings()

        #self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        #self.settings.screen_width = self.screen.get_rect().width
        #self.settings.screen_height = self.screen.get_rect().height

        self.screen = pygame.display.set_mode(
            (self.settings.screen_width, self.settings.screen_height ))
        pygame.display.set_caption("Alien Invasion")

        # Create an instance to store game stats.
        self.stats = GameStats(self)
        # Create scoreboard
        self.scoreboard = Scoreboard(self)

        # Create objects
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # Make play button
        self.play_button = Button(self, "Play")


    def run_game(self):
        """Start the main loop for the game"""
        while True:
            # Watch for keyboard and mouse events
            self._check_events()
            if self.stats.game_active:
                # Updates ship's movement
                self.ship.update()

                # Update bullets
                self._bullets_update()

                # Update aliens
                self._aliens_update()
            # Redraw the screen during each pass through the loop
            self._update_screen()

            # Make themost recently drawn screen visible
            pygame.display.flip()


    def _check_events(self):
        """ Responds to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keyDown_events(event)
            elif event.type == pygame.KEYUP:
               self._check_keyUP_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_keyDown_events(self, event):
        """ Responds to keypresses."""
        if event.key == pygame.K_RIGHT:
            # Move the ship to the right
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullet()

    def _check_keyUP_events(self, event):
        """ Responds to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False



    def _update_screen(self):
        """ Updates the images on the screen, and flip to the new screen."""
        self.screen.fill(self.settings.bg_color)
        self.ship.blitme()
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.aliens.draw(self.screen)

        # Draw score information
        self.scoreboard.show_score()

        if not self.stats.game_active:
            self.play_button.draw_button()

    def _fire_bullet(self):
        """ Create a new bullet each time spacebar is pressed and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)


    def _remove_bullets(self):
        for bullet in  self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

    def _create_fleet(self):
        """ Create fleet of aliens """
        # Make an alien and find the amount of aliens in a row
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        available_space_x = self.settings.screen_width-(2 * alien_width)
        number_aliens_x = available_space_x // (2* alien_width)

        # Determine the amount of  alien rows
        ship_height = self.ship.rect.height
        available_space_y = (self.settings.screen_height - (3 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # Create full fleet
        for row_number in range (number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        alien = Alien(self)
        alien_width = alien.rect.width
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
        self.aliens.add(alien)

    def _bullets_update(self):
        self.bullets.update()
        self._remove_bullets()
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """ Check for any bullets if they have hit an alien and if so then get rid of the alien. Also spawns new fleet if last fleet is annihalated"""
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
        if collisions:
            for hits in collisions.values():
                self.stats.score += self.settings.alien_points * len(hits)
            self.scoreboard.prep_score()
            self.scoreboard.check_high_score()
            
 
        if not self.aliens:
            #Destroy existing bullets and spawn new fleet
            self.bullets.empty()
            self._create_fleet()

            # Level up
            self.settings.level_up()
            self.stats.level += 1
            self.scoreboard.prep_level()


    def _aliens_update(self):
        """ Updates the aliens positions."""
        self._check_fleet_edges()
        self.aliens.update()
        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
        # Look for aliens reaching bottom of the screen
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """ Drop the entire fleet one row and chenge the fleet's direction. """
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _ship_hit(self):
        """ Respond to the ship being hit by an alien."""
        if self.stats.ships_left > 0:
            # Decrement ships_left.
            self.stats.ships_left -= 1
            self.scoreboard.prep_ships()

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Pause
            sleep(0.5)
        else:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)

    def _check_aliens_bottom(self):
        """ Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Treat the same as if ship got hit.
                self._ship_hit()
                break

    def _check_play_button(self, mouse_pos):
        """ Start a new game when player clicks Play."""
        if self.play_button.rect.collidepoint(mouse_pos) and not self.stats.game_active:
            self.stats.reset_stats()
            self.settings.initialize_dynamic_settings()
            self.stats.game_active = True

            #Hide mouse cursor
            pygame.mouse.set_visible(False)

            # Get rid of any leftover aliens and bullets
            self.aliens.empty()
            self.bullets.empty()

            #Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            self.scoreboard.prep_score()
            self.scoreboard.prep_high_score()
            self.scoreboard.prep_ships()

if __name__ == '__main__':

    # Make a game instance, and run the game
    ai = AlienInvasion()
    ai.run_game()

