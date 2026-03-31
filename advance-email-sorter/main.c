#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <pthread.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <errno.h>
#include <signal.h>
#include <time.h>
#include <sys/stat.h>
#include <sys/types.h>

#define MAX_EMAIL_LENGTH 256
#define MAX_DOMAIN_LENGTH 128
#define MAX_LINE_LENGTH 512
#define NUM_THREADS 10
#define MAX_PROVIDERS 100

// Configuration
#define DEFAULT_INPUT_FILE "emails.txt"
#define DEFAULT_OUTPUT_FOLDER "output"

// Mutex for thread safety
pthread_mutex_t file_mutex = PTHREAD_MUTEX_INITIALIZER;

// Global variables for pause/resume/stop
volatile sig_atomic_t running = 1;
volatile sig_atomic_t paused = 0;

// Global array to track progress
long thread_positions[NUM_THREADS];

// Structure for thread arguments
typedef struct {
    char input_file[256];
    char output_folder[256];
    long start_pos;
    long end_pos;
    int thread_id;
} ThreadArgs;

// Structure to hold provider information
typedef struct {
    char name[64];
    int count;
} ProviderInfo;

ProviderInfo providers[MAX_PROVIDERS];
int provider_count = 0;

// Function to handle signals (pause, resume, stop)
void signal_handler(int signo) {
    if (signo == SIGINT) {
        running = 0;
    } else if (signo == SIGUSR1) {
        paused = 1;
    } else if (signo == SIGUSR2) {
        paused = 0;
    }
}

// Function to check email syntax
bool check_syntax(const char *email) {
    const char *at = strchr(email, '@');
    if (at == NULL || at == email || *(at + 1) == '\0') return false;
    if (strchr(at + 1, '.') == NULL) return false;
    return true;
}

// Function to check DNS records and SMTP connection
// Combines both to avoid redundant resolutions
bool verify_email(const char *email) {
    char domain[MAX_DOMAIN_LENGTH];
    const char *at = strchr(email, '@');
    if (at == NULL) return false;
    strncpy(domain, at + 1, MAX_DOMAIN_LENGTH - 1);
    domain[MAX_DOMAIN_LENGTH - 1] = '\0';

    struct addrinfo hints, *res;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(domain, "25", &hints, &res) != 0) {
        return false;
    }

    bool success = false;
    int sock = socket(res->ai_family, res->ai_socktype, res->ai_protocol);
    if (sock >= 0) {
        struct timeval tv;
        tv.tv_sec = 2;
        tv.tv_usec = 0;
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&tv, sizeof tv);
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&tv, sizeof tv);

        if (connect(sock, res->ai_addr, res->ai_addrlen) == 0) {
            success = true;
        }
        close(sock);
    }

    freeaddrinfo(res);
    return success;
}

// Function to detect provider
const char* detect_provider(const char *email) {
    char domain[MAX_DOMAIN_LENGTH];
    const char *at = strchr(email, '@');
    if (at == NULL) return "Unknown";
    strncpy(domain, at + 1, MAX_DOMAIN_LENGTH - 1);
    domain[MAX_DOMAIN_LENGTH - 1] = '\0';

    // --- Security Providers (Specific) ---
    if (strstr(domain, "messagelabs") != NULL) return "MessageLabs";
    if (strstr(domain, "mimecast") != NULL) return "Mimecast";
    if (strstr(domain, "pphosted") != NULL) return "Proofpoint";
    if (strstr(domain, "barracuda") != NULL) return "Barracuda";
    if (strstr(domain, "sophos") != NULL) return "Sophos";
    if (strstr(domain, "trendmicro") != NULL) return "TrendMicro";

    // --- Regional & Branded ISPs (Specific) ---
    if (strstr(domain, "comcast") != NULL) return "Comcast";
    if (strstr(domain, "charter") != NULL) return "Charter";
    if (strstr(domain, "cox.net") != NULL) return "Cox";
    if (strstr(domain, "sky.com") != NULL) return "Sky";
    if (strstr(domain, "bt.prod.cloud.openwave.ai") != NULL) return "BT";
    if (strstr(domain, "virginmedia") != NULL) return "VirginMedia";
    if (strstr(domain, "talktalk") != NULL) return "TalkTalk";
    if (strstr(domain, "earthlink") != NULL) return "Earthlink";
    if (strstr(domain, "windstream") != NULL) return "Windstream";
    if (strstr(domain, "orange.fr") != NULL || strstr(domain, "wanadoo.fr") != NULL) return "Orange";
    if (strstr(domain, "free.fr") != NULL) return "Free.fr";
    if (strstr(domain, "libero.it") != NULL) return "Libero";
    if (strstr(domain, "virgilio.it") != NULL) return "Virgilio";
    if (strstr(domain, "tiscali.it") != NULL) return "Tiscali";
    if (strstr(domain, "seznam.cz") != NULL) return "Seznam";
    if (strstr(domain, "t-online.de") != NULL) return "T-online";
    if (strstr(domain, "swisscom") != NULL) return "Swisscom";
    if (strstr(domain, "bluenet.ch") != NULL) return "Bluewin";
    if (strstr(domain, "post.ch") != NULL) return "SwissPost";
    if (strstr(domain, "biglobe.ne.jp") != NULL) return "Biglobe";
    if (strstr(domain, "so-net.ne.jp") != NULL) return "So-net";
    if (strstr(domain, "rakuten") != NULL) return "Rakuten";
    if (strstr(domain, "uol.com.br") != NULL || strstr(domain, "bol.com.br") != NULL) return "UOL";
    if (strstr(domain, "terra.com.br") != NULL) return "Terra";
    if (strstr(domain, "telstra") != NULL) return "Telstra";
    if (strstr(domain, "optusnet") != NULL) return "Optus";
    if (strstr(domain, "rogers.com") != NULL) return "Rogers";
    if (strstr(domain, "shaw.ca") != NULL) return "Shaw";

    // --- Specific Hosting Providers ---
    if (strstr(domain, "secureserver.net") != NULL) return "GoDaddy";
    if (strstr(domain, "emailsrvr.com") != NULL) return "Rackspace";
    if (strstr(domain, "1and1") != NULL) return "IONOS";
    if (strstr(domain, "hostgator") != NULL) return "HostGator";
    if (strstr(domain, "bluehost") != NULL) return "Bluehost";
    if (strstr(domain, "siteground") != NULL) return "SiteGround";
    if (strstr(domain, "privateemail.com") != NULL) return "NameCheap";
    if (strstr(domain, "networksolutions") != NULL) return "NetworkSolutions";
    if (strstr(domain, "hinet.net") != NULL) return "Hinet";
    if (strstr(domain, "hibox") != NULL) return "Hibox";
    if (strstr(domain, "nominalia") != NULL) return "Nominalia";
    if (strstr(domain, "nifty.com") != NULL) return "Nifty";
    if (strstr(domain, "ocn.ad.jp") != NULL) return "OCN";
    if (strstr(domain, "netnavigator") != NULL) return "Netnavigator";
    if (strstr(domain, "mweb.co.za") != NULL) return "Mweb";
    if (strstr(domain, "mycloudmailbox") != NULL) return "MyCloudMailbox";
    if (strstr(domain, "sherwebcloud") != NULL) return "SherwebCloud";
    if (strstr(domain, "ovh.net") != NULL) return "OVH";
    if (strstr(domain, "one.com") != NULL) return "One.com";

    // --- Major Global Providers (Generic/Infrastructure) ---
    if (strstr(domain, "google") != NULL) return "Gmail";
    if (strstr(domain, "icloud") != NULL || strstr(domain, "apple.com") != NULL) return "Apple";
    if (strstr(domain, "protection.outlook.com") != NULL || strstr(domain, "eo.outlook.com") != NULL || strstr(domain, "outlook.com") != NULL) return "Office365";
    if (strstr(domain, "aol") != NULL) return "Aol";
    if (strstr(domain, "yahoodns") != NULL || strstr(domain, "yahoomail") != NULL) return "Yahoo";
    if (strstr(domain, "protonmail") != NULL) return "Protonmail";
    if (strstr(domain, "zoho") != NULL) return "Zoho";
    if (strstr(domain, "yandex") != NULL) return "Yandex";
    if (strstr(domain, "mail.ru") != NULL) return "Mail.ru";
    if (strstr(domain, "fastmail") != NULL || strstr(domain, "messagingengine") != NULL) return "Fastmail";
    if (strstr(domain, "gmx") != NULL) return "GMX";
    if (strstr(domain, "web.de") != NULL) return "Web.de";
    if (strstr(domain, "mail.com") != NULL) return "Mail.com";

    // --- Chinese Providers ---
    if (strstr(domain, "qq.com") != NULL) return "QQ";
    if (strstr(domain, "netease") != NULL || strstr(domain, "163.com") != NULL || strstr(domain, "126.com") != NULL) return "Netease";
    if (strstr(domain, "aliyun") != NULL) return "Aliyun";
    if (strstr(domain, "sina") != NULL) return "Sina";
    if (strstr(domain, "21cn") != NULL) return "21cn";
    if (strstr(domain, "263.net") != NULL) return "263";
    if (strstr(domain, "hanmail") != NULL) return "Hanmail";
    if (strstr(domain, "daum") != NULL) return "Daum";
    if (strstr(domain, "naver.com") != NULL) return "Naver";

    // --- Generic Webmail / Hosting Panels ---
    if (strstr(domain, "zimbra") != NULL) return "Zimbra";
    if (strstr(domain, "roundcube") != NULL) return "Roundcube";
    if (strstr(domain, "webmail") != NULL || strstr(domain, "cpanel") != NULL || strstr(domain, "plesk") != NULL || strstr(domain, "directadmin") != NULL || strstr(domain, "mailhost") != NULL) return "Webmail";

    return "Unknown";
}

// Function to write to file with thread safety
void write_to_file(const char *filename, const char *email) {
    pthread_mutex_lock(&file_mutex);
    FILE *fp = fopen(filename, "a");
    if (fp != NULL) {
        fprintf(fp, "%s\n", email);
        fclose(fp);
    }
    pthread_mutex_unlock(&file_mutex);
}

// Function to update provider counts
void update_provider_count(const char *provider) {
    pthread_mutex_lock(&file_mutex);
    int found = 0;
    for (int i = 0; i < provider_count; i++) {
        if (strcmp(providers[i].name, provider) == 0) {
            providers[i].count++;
            found = 1;
            break;
        }
    }
    if (!found) {
        if (provider_count < MAX_PROVIDERS) {
            strncpy(providers[provider_count].name, provider, 63);
            providers[provider_count].name[63] = '\0';
            providers[provider_count].count = 1;
            provider_count++;
        }
    }
    pthread_mutex_unlock(&file_mutex);
}

// Thread function
void *process_email(void *arg) {
    ThreadArgs *args = (ThreadArgs*) arg;
    char input_file[256];
    char output_folder[256];
    long start_pos;
    long end_pos;
    int thread_id;

    strcpy(input_file, args->input_file);
    strcpy(output_folder, args->output_folder);
    start_pos = args->start_pos;
    end_pos = args->end_pos;
    thread_id = args->thread_id;

    FILE *fp = fopen(input_file, "r");
    if (fp == NULL) {
        pthread_exit(NULL);
    }

    fseek(fp, start_pos, SEEK_SET);

    char line[MAX_LINE_LENGTH];
    long current_pos = start_pos;

    // Skip the first partial line if we're not at the start
    if (start_pos != 0) {
        if (fgets(line, MAX_LINE_LENGTH, fp)) {
            current_pos = ftell(fp);
        }
    }

    while (running && current_pos < end_pos && fgets(line, MAX_LINE_LENGTH, fp) != NULL) {
        thread_positions[thread_id] = current_pos;

        while (paused && running) {
            sleep(1);
        }

        line[strcspn(line, "\r\n")] = 0;
        if (strlen(line) == 0) {
            current_pos = ftell(fp);
            continue;
        }

        char email[MAX_EMAIL_LENGTH];
        strncpy(email, line, MAX_EMAIL_LENGTH - 1);
        email[MAX_EMAIL_LENGTH - 1] = '\0';

        bool is_valid = check_syntax(email) && verify_email(email);
        const char *provider = detect_provider(email);

        char valid_file[512];
        char invalid_file[512];
        char provider_file[512];

        snprintf(valid_file, sizeof(valid_file), "%s/valid.txt", output_folder);
        snprintf(invalid_file, sizeof(invalid_file), "%s/invalid.txt", output_folder);
        snprintf(provider_file, sizeof(provider_file), "%s/%s.txt", output_folder, provider);

        if (is_valid) {
            write_to_file(valid_file, email);
            write_to_file(provider_file, email);
        } else {
            write_to_file(invalid_file, email);
        }

        update_provider_count(provider);
        current_pos = ftell(fp);
    }

    thread_positions[thread_id] = current_pos;
    fclose(fp);
    pthread_exit(NULL);
}

// Function to print progress
void *print_progress(void *arg) {
    const char *input_file = (const char *)arg;
    FILE *fp = fopen(input_file, "r");
    if (fp == NULL) return NULL;
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fclose(fp);

    if (file_size == 0) file_size = 1;

    while (running) {
        long processed = 0;
        for (int i = 0; i < NUM_THREADS; i++) {
            processed += thread_positions[i];
        }

        double progress = (double)processed / file_size * 100.0;
        if (progress > 100.0) progress = 100.0;
        printf("Progress: %.2f%%\r", progress);
        fflush(stdout);
        sleep(1);
    }
    printf("\n");
    return NULL;
}

int main(int argc, char *argv[]) {
    // Signal handling setup
    struct sigaction sa;
    sa.sa_handler = signal_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGUSR1, &sa, NULL);
    sigaction(SIGUSR2, &sa, NULL);

    char *input_file = (char*)DEFAULT_INPUT_FILE;
    char *output_folder = (char*)DEFAULT_OUTPUT_FOLDER;

    if (argc > 1) {
        input_file = argv[1];
    }
    if (argc > 2) {
        output_folder = argv[2];
    }

    // Create output folder if it doesn't exist
    struct stat st = {0};
    if (stat(output_folder, &st) == -1) {
        if (mkdir(output_folder, 0777) != 0) {
            perror("Error creating output folder");
            return 1;
        }
    }

    // Get file size
    FILE *fp = fopen(input_file, "r");
    if (fp == NULL) {
        perror("Error opening input file");
        return 1;
    }
    fseek(fp, 0, SEEK_END);
    long file_size = ftell(fp);
    fclose(fp);

    // Initialize progress tracking
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_positions[i] = 0;
    }

    // Calculate chunk size for each thread
    long chunk_size = file_size / NUM_THREADS;

    pthread_t threads[NUM_THREADS];
    ThreadArgs args[NUM_THREADS];

    for (int i = 0; i < NUM_THREADS; i++) {
        args[i].thread_id = i;
        strncpy(args[i].input_file, input_file, 255);
        strncpy(args[i].output_folder, output_folder, 255);
        args[i].start_pos = i * chunk_size;
        args[i].end_pos = (i == NUM_THREADS - 1) ? file_size : (i + 1) * chunk_size;

        if (pthread_create(&threads[i], NULL, process_email, (void *)&args[i])) {
            perror("Error creating thread");
            return 1;
        }
    }

    // Start progress printing thread
    pthread_t progress_thread;
    if (pthread_create(&progress_thread, NULL, print_progress, (void*)input_file)) {
        perror("Error creating progress thread");
        return 1;
    }

    // Wait for threads to complete
    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    running = 0;
    pthread_join(progress_thread, NULL);

    // Print provider breakdown
    printf("\nProvider Breakdown:\n");
    for (int i = 0; i < provider_count; i++) {
        printf("%s: %d\n", providers[i].name, providers[i].count);
    }

    printf("Email sorting complete.\n");
    return 0;
}
