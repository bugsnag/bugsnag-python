require "fileutils"

Maze.hooks.before_all do
  # log to console, not the filesystem
  Maze.config.file_log = false
  Maze.config.log_requests = true

  # don't wait so long for requests/not to receive requests
  Maze.config.receive_requests_wait = 10
  Maze.config.receive_no_requests_wait = 10

  # warn if a test takes more than 5 seconds to send a request
  Maze.config.receive_requests_slow_threshold = 5

  # bugsnag-python doesn't need to send the integrity header
  Maze.config.enforce_bugsnag_integrity = false

  # install bugsnag into each fixture
  Dir.each_child("features/fixtures") do |path|
    fixture_directory = "#{Dir.pwd}/features/fixtures/#{path}"

    next unless File.directory?(fixture_directory)

    destination = "#{fixture_directory}/temp-bugsnag-python"

    FileUtils.mkdir(destination) unless File.exist?(destination)

    FileUtils.cp_r(
      ["bugsnag", "setup.py"],
      destination,
      remove_destination: true # delete destination before copying
    )

    at_exit do
      FileUtils.rm_rf(destination)
    end
  end
end

Maze.hooks.before do
  host = "host.docker.internal"

  Maze::Runner.environment["BUGSNAG_API_KEY"] = $api_key
  Maze::Runner.environment["BUGSNAG_ERROR_ENDPOINT"] = "http://#{host}:#{Maze.config.port}/notify"
  Maze::Runner.environment["BUGSNAG_SESSION_ENDPOINT"] = "http://#{host}:#{Maze.config.port}/sessions"
end
